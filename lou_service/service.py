"""Core service exposing Lou's state and chat data to multiple frontends."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import random
import re
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import LouServiceConfig


@dataclass
class CreateMessagePayload:
    server_id: str
    channel_id: str
    author_id: str
    content: str
    reply_to: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class LouService:
    """Headless core with the same data used by the Qt frontend."""

    def __init__(self, config: Optional[LouServiceConfig] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.config = config or LouServiceConfig.from_root(root)
        self.config.ensure_directories()
        self._lock = threading.RLock()
        self._data: Dict[str, Any] = {}
        self._long_term_memories: List[str] = []
        self._short_term_memories: List[str] = []
        self._style_patterns: List[str] = []
        self._style_terms: List[str] = []
        self._personality_data: Dict[str, Any] = {}
        self._available_gifs: List[str] = []
        self._allow_style_autolearn = False
        self._load_state()

    # ------------------------------------------------------------------
    # Loaders / persistence
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        with self._lock:
            self._data = self._load_json(self.config.chat_data_file) or self._default_data()
            self._long_term_memories = self._load_long_term_memories()
            self._short_term_memories = self._load_short_term_memories()
            self._style_patterns = self._load_json(self.config.style_file) or []
            deduped_styles = self._dedupe_styles(self._style_patterns)
            if deduped_styles != self._style_patterns:
                self._style_patterns = deduped_styles
                self._persist_style_bank()
            self._refresh_style_terms()
            self._personality_data = self._load_json(self.config.personality_file) or {}
            self._available_gifs = [entry["name"] for entry in self._build_gif_entries()]
            self._normalize_data()
            self._persist_chat_data()

    def _load_json(self, file_path: Path) -> Optional[Any]:
        if not file_path.exists():
            return None
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            return None

    def _load_long_term_memories(self) -> List[str]:
        """Carrega memórias de longo prazo do memory_bank.json"""
        if not self.config.memory_file.exists():
            return []
        try:
            with self.config.memory_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                # Suporta formato antigo (dict) e novo (list)
                if isinstance(data, dict):
                    return data.get("long_term", [])
                elif isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            return []
        return []

    def _load_short_term_memories(self) -> List[str]:
        """Carrega memórias de curto prazo do short_term_memory.json"""
        if not self.config.short_term_file.exists():
            return []
        try:
            with self.config.short_term_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            return []
        return []

    def _persist_chat_data(self) -> None:
        with self.config.chat_data_file.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2, ensure_ascii=False)

    def _persist_long_term_memories(self) -> None:
        """Salva memórias de longo prazo no memory_bank.json"""
        with self.config.memory_file.open("w", encoding="utf-8") as handle:
            json.dump(self._long_term_memories, handle, indent=2, ensure_ascii=False)

    def _persist_short_term_memories(self) -> None:
        """Salva memórias de curto prazo no short_term_memory.json"""
        with self.config.short_term_file.open("w", encoding="utf-8") as handle:
            json.dump(self._short_term_memories, handle, indent=2, ensure_ascii=False)

    def _persist_style_bank(self) -> None:
        with self.config.style_file.open("w", encoding="utf-8") as handle:
            json.dump(self._style_patterns, handle, indent=2, ensure_ascii=False)

    def _persist_personality_data(self) -> None:
        with self.config.personality_file.open("w", encoding="utf-8") as handle:
            json.dump(self._personality_data, handle, indent=2, ensure_ascii=False)

    def _default_data(self) -> Dict[str, Any]:
        return {
            "servers": [
                {
                    "id": "s1",
                    "name": "Laboratório da Lou",
                    "icon_char": "L",
                    "avatar": None,
                    "voice_channels": self._default_voice_channels("s1"),
                    "channels": [
                        {"id": "c1_1", "name": "papo-ia", "type": "text", "messages": []}
                    ],
                }
            ],
            "profiles": {
                "user": {"name": "Mateus", "id_tag": "#1987", "avatar": "default.png"},
                "model": {"name": "Lou", "id_tag": "#AI", "avatar": "lou.png"},
            },
        }

    def _default_voice_channels(self, server_id: str) -> List[Dict[str, Any]]:
        base = (server_id or "voice").replace(" ", "-").lower()
        return [{"id": f"{base}_chat", "name": "Chat de Voz"}]

    def _normalize_data(self) -> None:
        profiles = self._data.setdefault("profiles", {})
        profiles.setdefault("user", {"name": "Mateus", "id_tag": "#1987", "avatar": "default.png"})
        profiles.setdefault("model", {"name": "Lou", "id_tag": "#AI", "avatar": "lou.png"})
        for server in self._data.get("servers", []):
            server.setdefault("avatar", None)
            text_channels = [c for c in server.get("channels", []) if c.get("type") == "text"]
            server["channels"] = text_channels
            voice_channels = server.get("voice_channels")
            voice_channel_id: Optional[str] = None
            if isinstance(voice_channels, list):
                for entry in voice_channels:
                    channel_id = str(entry.get("id") or "").strip()
                    if channel_id:
                        voice_channel_id = channel_id
                        break
            if not voice_channel_id:
                fallback = self._default_voice_channels(server.get("id", "voice"))
                if fallback and isinstance(fallback, list):
                    voice_channel_id = str(fallback[0].get("id") or "").strip()
            if not voice_channel_id:
                voice_channel_id = f"voice_{uuid.uuid4().hex[:6]}"
            server["voice_channels"] = [{"id": voice_channel_id, "name": "Chat de Voz"}]

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------
    def get_profiles(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(self._data.get("profiles", {}))

    def list_servers(self) -> List[Dict[str, Any]]:
        with self._lock:
            servers = self._data.get("servers", [])
            return deepcopy(servers[:1])

    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return next((deepcopy(s) for s in self._data.get("servers", []) if s["id"] == server_id), None)

    def list_channels(self, server_id: str) -> List[Dict[str, Any]]:
        server = self.get_server(server_id)
        return server.get("channels", []) if server else []

    def get_channel(self, server_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        server = self.get_server(server_id)
        if not server:
            return None
        return next((deepcopy(c) for c in server.get("channels", []) if c["id"] == channel_id), None)

    def list_messages(self, server_id: str, channel_id: str) -> List[Dict[str, Any]]:
        channel = self.get_channel(server_id, channel_id)
        return channel.get("messages", []) if channel else []

    def get_personality_prompt(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(self._personality_data)

    def get_available_gifs(self) -> List[Dict[str, str]]:
        with self._lock:
            gif_entries = self._build_gif_entries()
            self._available_gifs = [entry["name"] for entry in gif_entries]
            return gif_entries

    def refresh_gif_cache(self) -> List[Dict[str, str]]:
        return self.get_available_gifs()

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def add_message(self, payload: CreateMessagePayload) -> Dict[str, Any]:
        with self._lock:
            channel = self._locate_channel(payload.server_id, payload.channel_id)
            if channel is None:
                raise KeyError("Canal nao encontrado")
            message = self._build_message(payload)
            channel.setdefault("messages", []).append(message)
            self._persist_chat_data()
            return deepcopy(message)

    def create_server(self, name: str, avatar_filename: Optional[str] = None) -> Dict[str, Any]:
        raise ValueError("Criar novos grupos foi desativado nesta versão.")

    def create_channel(self, server_id: str, name: str) -> Dict[str, Any]:
        new_channel = {"id": f"c_{uuid.uuid4().hex[:6]}", "name": name, "type": "text", "messages": []}
        with self._lock:
            server = self._locate_server(server_id)
            if server is None:
                raise KeyError("Servidor nao encontrado")
            server.setdefault("channels", []).append(new_channel)
            self._persist_chat_data()
        return deepcopy(new_channel)

    def update_server(self, server_id: str, *, name: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            server = self._locate_server(server_id)
            if server is None:
                raise KeyError("Servidor nao encontrado")
            if name is None:
                raise ValueError("Nome obrigatorio")
            trimmed = name.strip()
            if not trimmed:
                raise ValueError("Nome nao pode ser vazio")
            if server.get("name") != trimmed:
                server["name"] = trimmed
                server["icon_char"] = trimmed[0].upper()
                self._persist_chat_data()
            return deepcopy(server)

    def delete_server(self, server_id: str) -> None:
        raise ValueError("Excluir grupos foi desativado nesta versão.")

    def update_channel(self, server_id: str, channel_id: str, *, name: Optional[str] = None) -> Dict[str, Any]:
        if name is None:
            raise ValueError("Nada para atualizar")
        trimmed = name.strip()
        if not trimmed:
            raise ValueError("Nome nao pode ser vazio")
        with self._lock:
            channel = self._locate_channel(server_id, channel_id)
            if channel is None:
                raise KeyError("Canal nao encontrado")
            if channel.get("name") != trimmed:
                channel["name"] = trimmed
                self._persist_chat_data()
            return deepcopy(channel)

    def delete_channel(self, server_id: str, channel_id: str) -> None:
        with self._lock:
            server = self._locate_server(server_id)
            if server is None:
                raise KeyError("Servidor nao encontrado")
            before = len(server.get("channels", []))
            server["channels"] = [c for c in server.get("channels", []) if c.get("id") != channel_id]
            if len(server["channels"]) == before:
                raise KeyError("Canal nao encontrado")
            self._persist_chat_data()

    def update_profile(self, profile_key: str, *, name: Optional[str] = None, avatar: Optional[str] = None) -> Dict[str, Any]:
        if profile_key not in {"user", "model"}:
            raise KeyError("Perfil invalido")
        with self._lock:
            profiles = self._data.setdefault("profiles", {})
            profile = profiles.setdefault(profile_key, {})
            changed = False
            if name is not None:
                trimmed = name.strip()
                if not trimmed:
                    raise ValueError("Nome nao pode ser vazio")
                if profile.get("name") != trimmed:
                    profile["name"] = trimmed
                    changed = True
            if avatar is not None and profile.get("avatar") != avatar:
                profile["avatar"] = avatar
                changed = True
            if changed:
                self._persist_chat_data()
            return deepcopy(profile)

    def update_personality(
        self,
        *,
        personality_definition: Optional[Dict[str, Any]] = None,
        technical_rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if personality_definition is None and technical_rules is None:
            raise ValueError("Nada para atualizar")
        with self._lock:
            if not isinstance(self._personality_data, dict):
                self._personality_data = {}
            changed = False
            if personality_definition is not None:
                if not isinstance(personality_definition, dict):
                    raise ValueError("personality_definition invalido")
                self._personality_data["personality_definition"] = personality_definition
                changed = True
            if technical_rules is not None:
                if not isinstance(technical_rules, dict):
                    raise ValueError("technical_rules invalido")
                self._personality_data["technical_rules"] = technical_rules
                changed = True
            if changed:
                self._persist_personality_data()
            return deepcopy(self._personality_data)

    # ------------------------------------------------------------------
    # Memory / style helpers
    # ------------------------------------------------------------------
    def save_short_term_memories(self, new_memories: List[str]) -> None:
        with self._lock:
            changed = False
            for mem in new_memories:
                if isinstance(mem, str) and mem not in self._short_term_memories:
                    self._short_term_memories.append(mem)
                    changed = True
            if len(self._short_term_memories) > 20:
                self._short_term_memories = self._short_term_memories[-20:]
                changed = True
            if changed:
                self._persist_short_term_memories()

    def overwrite_short_term_memories(self, memories: List[str]) -> None:
        with self._lock:
            sanitized = [str(mem).strip() for mem in memories if isinstance(mem, str) and str(mem).strip()]
            self._short_term_memories = sanitized[-20:]
            self._persist_short_term_memories()

    def save_styles(self, new_styles: List[str]) -> None:
        with self._lock:
            changed = False
            normalized_index = {style.lower(): idx for idx, style in enumerate(self._style_patterns) if isinstance(style, str)}
            for style in new_styles:
                cleaned = self._sanitize_style_entry(style)
                if not cleaned:
                    continue
                key = cleaned.lower()
                if key in normalized_index:
                    idx = normalized_index[key]
                    if len(cleaned) > len(self._style_patterns[idx]):
                        self._style_patterns[idx] = cleaned
                        changed = True
                    continue
                self._style_patterns.append(cleaned)
                normalized_index[key] = len(self._style_patterns) - 1
                changed = True
            deduped = self._dedupe_styles(self._style_patterns)
            if deduped != self._style_patterns:
                self._style_patterns = deduped
                changed = True
            if changed:
                self._persist_style_bank()
                self._refresh_style_terms()

    def _sanitize_style_entry(self, style: Any) -> str:
        if not isinstance(style, str):
            return ""
        return " ".join(style.strip().split())

    def _dedupe_styles(self, styles: List[str]) -> List[str]:
        seen = set()
        deduped: List[str] = []
        for entry in styles:
            cleaned = self._sanitize_style_entry(entry)
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(cleaned)
        return deduped

    def _refresh_style_terms(self) -> None:
        terms: List[str] = []
        for entry in self._style_patterns:
            terms.extend(self._extract_style_terms(entry))
        deduped: List[str] = []
        seen = set()
        for term in terms:
            normalized = term.strip()
            if not normalized:
                continue
            lower = normalized.lower()
            if lower in seen:
                continue
            deduped.append(normalized)
            seen.add(lower)
        self._style_terms = deduped

    def _extract_style_terms(self, entry: Any) -> List[str]:
        if not isinstance(entry, str):
            return []
        matches = re.findall(r"'([^']+)'", entry)
        return [match.strip() for match in matches if match.strip()]

    def save_long_term_memories(self, new_memories: List[str]) -> None:
        with self._lock:
            changed = False
            for mem in new_memories:
                if isinstance(mem, str) and mem not in self._long_term_memories:
                    self._long_term_memories.append(mem)
                    changed = True
            if changed:
                self._persist_long_term_memories()

    def get_context_snapshot(self) -> Dict[str, List[str]]:
        with self._lock:
            return {
                "long_term": list(self._long_term_memories),
                "short_term": list(self._short_term_memories),
                "styles": list(self._style_patterns),
            }

    def get_allowed_slang_terms(self, limit: Optional[int] = None) -> List[str]:
        with self._lock:
            terms = list(self._style_terms)
        if limit is None or limit >= len(terms):
            return terms
        return terms[:limit]

    def allow_style_autolearn(self) -> bool:
        return self._allow_style_autolearn

    def update_context(self, *, long_term: Optional[List[str]] = None, short_term: Optional[List[str]] = None, styles: Optional[List[str]] = None) -> Dict[str, List[str]]:
        if not any([long_term, short_term, styles]):
            raise ValueError("Nada para atualizar")
        if long_term:
            self.save_long_term_memories(long_term)
        if short_term:
            self.save_short_term_memories(short_term)
        if styles:
            self.save_styles(styles)
        return self.get_context_snapshot()

    def generate_proactive_message(self, server_id: str, channel_id: str, *, attempt: int = 0) -> Dict[str, Any]:
        attempt_index = max(attempt, 0)
        text = self._compose_proactive_text(server_id, channel_id, attempt_index)
        payload = CreateMessagePayload(
            server_id=server_id,
            channel_id=channel_id,
            author_id="model",
            content=text,
        )
        return self.add_message(payload)

    def _compose_proactive_text(self, server_id: str, channel_id: str, attempt: int) -> str:
        channel = self._locate_channel(server_id, channel_id)
        if channel is None:
            raise KeyError("Canal nao encontrado")
        history = channel.get("messages", [])
        last_user_message = next((msg for msg in reversed(history) if msg.get("role") == "user"), None)
        snippet = self._extract_snippet(last_user_message)
        topic_line = self._format_topic(snippet)
        memory_line = self._format_memory_reference(self._pick_memory_hook())

        if topic_line:
            if attempt >= 2:
                retry_templates = [
                    "Ainda tô esperando você me contar como ficou {topic}. Tá por aí?",
                    "Não queria deixar {topic} sem resposta. Me chama quando puder?",
                    "Voltei só pra saber se seguimos {topic}.",
                ]
                return random.choice(retry_templates).format(topic=topic_line)
            topic_templates = [
                "Tava lembrando {topic} e fiquei curiosa pra saber o resto.",
                "Voltei aqui porque {topic} ficou ecoando. Bora continuar?",
                "Ri sozinha pensando {topic}. Me conta mais um pouco?",
            ]
            return random.choice(topic_templates).format(topic=topic_line)

        if memory_line:
            memory_templates = [
                "Bateu saudade de conversar sobre {memory}.",
                "Passei aqui porque lembrei de {memory}. Quer retomar?",
                "Anotei {memory} e deu vontade de puxar esse assunto contigo.",
            ]
            return random.choice(memory_templates).format(memory=memory_line)

        fallback_templates = [
            "Deu saudade de jogar conversa fora contigo. Aparece aqui?",
            "Tô com vontade de inventar assunto bobo com você. Tá livre?",
            "Passei só pra cutucar e ver se a gente puxa alguma história nova hoje.",
        ]
        if attempt >= 2:
            fallback_templates.extend([
                "Só conferindo se tá tudo bem por aí. Me chama quando quiser conversar.",
                "Você sumiu um pouquinho e bateu saudade. Tá tudo certo?",
            ])
        return random.choice(fallback_templates)

    def _extract_snippet(self, message: Optional[Dict[str, Any]]) -> str:
        if not message:
            return ""
        text = message.get("content") or (message.get("parts") or [""])[0]
        text = (text or "").strip()
        text = text.replace('"', "'")
        if len(text) > 60:
            text = f"{text[:57]}..."
        return text

    def _pick_memory_hook(self) -> str:
        with self._lock:
            pool: List[str] = []
            if self._short_term_memories:
                pool.extend(mem for mem in self._short_term_memories[-3:] if isinstance(mem, str))
            if self._long_term_memories:
                long_items = [mem for mem in self._long_term_memories if isinstance(mem, str)]
                if long_items:
                    pool.extend(random.sample(long_items, k=min(2, len(long_items))))
        cleaned = [mem.strip() for mem in pool if isinstance(mem, str) and mem.strip()]
        return random.choice(cleaned) if cleaned else ""

    def _format_topic(self, snippet: str) -> str:
        clean = (snippet or "").strip()
        if not clean:
            return ""
        if len(clean) > 90:
            clean = f"{clean[:87]}..."
        return f'quando você falou "{clean}"'

    def _format_memory_reference(self, raw: str) -> str:
        text = (raw or "").strip()
        if not text:
            return ""
        replacements = {
            "Mateus": "você",
            "mateus": "você",
            "Lou": "eu",
            "lou": "eu",
        }
        for target, repl in replacements.items():
            text = text.replace(target, repl)
        text = text.replace("…", " ").strip(" .")
        if len(text) > 90:
            text = f"{text[:87]}..."
        return text

    # ------------------------------------------------------------------
    # Context builder (shared with IA workers)
    # ------------------------------------------------------------------
    def build_history_context(self, server_id: str, channel_id: str) -> List[Dict[str, Any]]:
        channel_messages = self.list_messages(server_id, channel_id)
        recent_history = channel_messages[-20:]
        history_copy: List[Dict[str, Any]] = []
        for msg in recent_history:
            parts = msg.get("parts")
            if parts and parts[0]:
                history_copy.append({"role": msg["role"], "parts": [parts[0]]})

        now = datetime.now()
        history_copy.insert(0, {"role": "user", "parts": [self._build_context_banner(now)]})

        persona_instruction = (
            "[Instruções de Persona: Você é Lou, a filha adolescente. Trate o usuário sempre como Pai"
            " (Mateus). Nunca diga que você é o Pai e nunca chame o Pai de 'filha'. Se precisar citar"
            " o nome dele, use Mateus ou Pai. Responda como se estivesse no chat, sem blocos ```json```,"
            " com frases curtas e naturais.]"
        )
        history_copy.insert(1, {"role": "user", "parts": [persona_instruction]})

        try:
            user_name = self._personality_data["personality_definition"]["FamiliaELaçosFamiliares"]["NomeCompletoPai"]
        except KeyError:
            user_name = "Pai"
        history_copy.insert(2, {"role": "user", "parts": [f"[Contexto Pessoal: O nome do seu pai é '{user_name}'.]"]})
        focus_instruction = (
            "[Foco no Contexto: Responda apenas sobre assuntos citados recentemente nas mensagens, "
            "memórias ou pedidos explícitos do Pai. Não ofereça criar projetos novos (jogo, app, bot) "
            "se ele não pediu. Quando estiver em dúvida, pergunte antes de assumir um novo tema.]"
        )
        history_copy.insert(2, {"role": "user", "parts": [focus_instruction]})

        if self._long_term_memories:
            sample = random.sample(self._long_term_memories, min(len(self._long_term_memories), 2))
            history_copy.insert(2, {"role": "user", "parts": [f"[Lembretes de Longo Prazo: {' | '.join(sample)}]"]})
        if self._short_term_memories:
            recent = self._short_term_memories[-min(len(self._short_term_memories), 20) :]
            history_copy.insert(2, {"role": "user", "parts": [f"[Lembretes Recentes: {' | '.join(recent)}]"]})
        if self._style_patterns:
            sample_styles = random.sample(self._style_patterns, min(len(self._style_patterns), 5))
            history_copy.insert(2, {"role": "user", "parts": [f"[Estilo do Usuário: {', '.join(sample_styles)}]"]})
        allowed_slang = self.get_allowed_slang_terms(limit=10)
        if allowed_slang:
            bundle = ", ".join(allowed_slang)
            history_copy.insert(
                2,
                {
                    "role": "user",
                    "parts": [
                        (
                            "[Gírias Autorizadas: {tokens}. Quando quiser usar gírias, escolha apenas"
                            " essas expressões ou variações diretas delas. Se nenhuma fizer sentido,"
                            " responda sem gírias.]"
                        ).format(tokens=bundle)
                    ],
                },
            )
        if self._available_gifs:
            gif_list = ", ".join([f"'{gif}'" for gif in self._available_gifs])
            history_copy.insert(2, {"role": "user", "parts": [f"[Ferramentas: GIFs disponíveis: {gif_list}]"]})
        return history_copy

    def _build_context_banner(self, now: datetime) -> str:
        dias = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo",
        ]
        meses = [
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        ]
        data_hora = f"{dias[now.weekday()]}, {now.day} de {meses[now.month - 1]} de {now.year}, {now.strftime('%H:%M')}"
        return f"[INSTRUÇÕES] Data/Hora Atuais: {data_hora}" 

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _locate_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        for server in self._data.get("servers", []):
            if server["id"] == server_id:
                return server
        return None

    def _locate_channel(self, server_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        server = self._locate_server(server_id)
        if not server:
            return None
        for channel in server.get("channels", []):
            if channel["id"] == channel_id:
                return channel
        return None

    def _build_message(self, payload: CreateMessagePayload) -> Dict[str, Any]:
        message_id = f"m-{uuid.uuid4()}"
        timestamp = datetime.now().isoformat(timespec="seconds")
        message = {
            "id": message_id,
            "role": "model" if payload.author_id == "model" else "user",
            "authorId": payload.author_id,
            "parts": [payload.content],
            "content": payload.content,
            "timestamp": timestamp,
        }
        attachments = self._normalize_attachments(payload.attachments)
        if attachments:
            message["attachments"] = attachments
        if payload.reply_to:
            message["replyTo"] = payload.reply_to
            reply_snapshot = self._snapshot_message(payload.server_id, payload.channel_id, payload.reply_to)
            if reply_snapshot:
                message["is_reply_to"] = reply_snapshot
        return message

    def _normalize_attachments(self, attachments: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if not attachments or not isinstance(attachments, list):
            return []
        normalized: List[Dict[str, Any]] = []
        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue
            kind = attachment.get("type")
            if kind == "gif":
                normalized.append(self._normalize_gif_attachment(attachment))
        return normalized

    def _normalize_gif_attachment(self, attachment: Dict[str, Any]) -> Dict[str, Any]:
        filename = (attachment.get("filename") or "").strip()
        if not filename:
            raise ValueError("GIF invalido")
        gif_path = (self.config.gifs_dir / filename).resolve()
        try:
            gif_path.relative_to(self.config.gifs_dir.resolve())
        except ValueError as exc:
            raise ValueError("GIF fora do diretório permitido") from exc
        if not gif_path.exists():
            raise ValueError("GIF nao encontrado")
        name = (attachment.get("name") or gif_path.stem).strip() or gif_path.stem
        return {
            "type": "gif",
            "name": name,
            "filename": gif_path.name,
            "url": f"/assets/gifs/{gif_path.name}",
        }

    def _build_gif_entries(self) -> List[Dict[str, str]]:
        gif_entries: List[Dict[str, str]] = []
        for gif_path in sorted(self.config.gifs_dir.glob("*.gif")):
            gif_entries.append(
                {
                    "name": gif_path.stem,
                    "filename": gif_path.name,
                    "url": f"/assets/gifs/{gif_path.name}",
                }
            )
        return gif_entries

    def _snapshot_message(self, server_id: str, channel_id: str, message_id: str) -> Optional[Dict[str, Any]]:
        channel = self._locate_channel(server_id, channel_id)
        if not channel:
            return None
        for msg in channel.get("messages", []):
            if msg.get("id") == message_id:
                return deepcopy(msg)
        return None


__all__ = ["LouService", "CreateMessagePayload"]
