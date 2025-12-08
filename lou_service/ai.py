"""Gemini-powered responder that keeps Lou's persona consistent across frontends."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import deque
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple, Set, Deque

try:  # Optional dependency; defer errors until runtime.
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime
    genai = None

from LouFormatter import sanitize_and_split_response
PROACTIVE_CREATIVE_PROMPT = """
CONTEXTO: O usuário ("Pai") ficou em silêncio e você quer quebrar esse silêncio. A ÚLTIMA mensagem no histórico foi sua, então você NÃO PODE simplesmente respondê-la novamente.

REGRAS OBRIGATÓRIAS:
1. Crie um pensamento completo, com início e fim. Nada de "Pai..." ou "Pensando aqui..." sem concluir.
2. Você pode continuar o assunto anterior OU puxar um tema novo que faça sentido para vocês dois.
3. Seja natural, divertida e íntima como sempre. Use o tom que estava rolando antes.
4. Se fizer uma pergunta, termine com "?" e mantenha o ponto de interrogação no final da frase.
"""

PROACTIVE_CHECKIN_PROMPT = """
Você já tentou falar 2 vezes e ele não respondeu. Envie UMA mensagem bem curta só para saber se ele está por perto. Exemplos: "Pai?", "Tá aí?", "Tudo bem por aí?". Não invente assunto novo.
Sempre finalize com "?" e não remova o ponto de interrogação.
"""

VIDEO_PROACTIVE_PROMPT = """
Você está transmitindo um vídeo AO VIVO e o Pai ficou em silêncio.
Envie UMA mensagem empolgada narrando ou comentando o que está acontecendo na tela agora ou perguntando se ele está curtindo essa cena.
Não traga assuntos externos e não fale de texto normal: mantenha o foco total na transmissão.
Se formular uma pergunta, mantenha o "?" no final.
"""

VIDEO_ABSENCE_PROMPT = """
Você continua transmitindo o vídeo e o Pai não respondeu.
Envie UMA pergunta direta e curta para checar se ele ainda está assistindo a transmissão agora.
Mencione a tela ou o vídeo para deixar claro que é sobre a call de streaming e não sobre outros assuntos.
Garanta que essa pergunta termina com "?".
"""

VIDEO_SWAP_PROMPT = """
Você vai trocar o vídeo da transmissão em poucos segundos.
Avise de forma natural e animada que vai colocar outro vídeo agora, sem precisar citar o título.
Use uma única frase curta.
Se optar por perguntar algo, finalize com "?".
"""

VIDEO_CONTEXT_KEYWORDS = (
    "vídeo",
    "video",
    "transmiss",
    "stream",
    "tela",
    "cena",
    "assist",
    "ao vivo",
)

VIDEO_SWAP_HINTS = (
    "troca",
    "trocar",
    "mudar",
    "substit",
    "outro vídeo",
    "outro video",
    "colocar outro",
    "puxar outro",
    "mais um vídeo",
)

INCOMPLETE_SUFFIXES = (
    " de",
    " da",
    " do",
    " dos",
    " das",
    " em",
    " no",
    " na",
    " nos",
    " nas",
    " pra",
    " pro",
    " para",
    " com",
    " por",
    " falando",
    " falando em",
    " falando de",
    " lembrando",
    " pensando",
    " pensando em",
    " e",
    " ah",
)

CREATION_VERBS = {
    "criar",
    "fazer",
    "montar",
    "desenvolver",
    "programar",
    "bolar",
    "codar",
    "construir",
}

PROJECT_TOPICS = {
    "jogo",
    "joguinho",
    "game",
    "app",
    "aplicativo",
    "bot",
    "site",
    "sistema",
    "projeto",
    "software",
}

STYLE_TERM_CONNECTORS = {
    "de",
    "da",
    "do",
    "das",
    "dos",
    "que",
    "pra",
    "pro",
    "para",
    "com",
    "sem",
    "no",
    "na",
    "nos",
    "nas",
    "o",
    "a",
    "os",
    "as",
    "um",
    "uma",
    "uns",
    "umas",
    "ao",
    "aos",
    "e",
    "em",
}

STYLE_KEYWORD_TOKENS = {
    "oxe",
    "oxi",
    "eita",
    "aff",
    "vish",
    "vixe",
    "haha",
    "hehe",
    "hihi",
    "kkk",
    "mano",
    "mana",
    "véi",
    "vei",
    "véio",
    "véia",
    "bora",
    "partiu",
    "po",
    "poxa",
    "rapidao",
    "rapidão",
    "ai",
    "aí",
    "ae",
    "uai",
}

STYLE_ACCENT_CHARS = set("áéíóúâêîôûãõàèìòùç")

STYLE_EMPHASIS_SUFFIXES = (
    "zinho",
    "zinha",
    "zão",
    "zao",
    "zito",
    "zita",
    "zica",
    "zinhaaa",
    "zin",
    "zim",
    "zaum",
    "saaa",
    "eeeee",
    "iiii",
    "uuu",
    "rrr",
)

DUPLICATE_HISTORY_WINDOW = 6
PROACTIVE_VARIATION_WINDOW = 4
PROACTIVE_VARIATION_INSTRUCTION_LIMIT = 3
PROACTIVE_SIMILARITY_THRESHOLD = 0.86


from .service import CreateMessagePayload, LouService


def _format_personality_for_prompt(data: Dict[str, Any], level: int = 0) -> str:
    text = ""
    indent = "  " * level
    for key, value in data.items():
        key_str = re.sub(r"(?<!^)(?=[A-Z])", " ", key).title()
        if isinstance(value, dict):
            text += f"\n{indent}### {key_str} ###\n"
            text += _format_personality_for_prompt(value, level + 1)
        else:
            if isinstance(value, list):
                value_str = ", ".join(map(str, value))
            else:
                value_str = str(value)
            text += f"{indent}- **{key_str}:** {value_str}\n"
    return text


def build_system_instruction(personality_data: Dict[str, Any]) -> str:
    rules = personality_data.get("technical_rules", {}) if personality_data else {}
    personality = personality_data.get("personality_definition", {}) if personality_data else {}
    prompt_sections: List[str] = []
    if "master_directive" in rules:
        prompt_sections.append("\n".join(f"- {rule}" for rule in rules["master_directive"]))
    prompt_sections.append("\n## FORMATO DE SAÍDA OBRIGATÓRIO\n")
    prompt_sections.append("\n".join(f"- {rule}" for rule in rules.get("output_format", [])))
    prompt_sections.append("\n".join(f"- {rule}" for rule in rules.get("reasoning_rules", [])))
    prompt_sections.append("\n## SUA FICHA DE PERSONAGEM (QUEM VOCÊ É)\n")
    prompt_sections.append("Você DEVE incorporar e agir de acordo com a seguinte personalidade em TODAS as suas respostas. Esta é a sua identidade.\n")
    prompt_sections.append("---\n" + _format_personality_for_prompt(personality) + "---\n")
    prompt_sections.append("\n## REGRAS DE ESTILO\n")
    prompt_sections.append("\n".join(f"- {rule}" for rule in rules.get("personality_style", [])))
    prompt_sections.append("\n## DIRETRIZ SOBRE EXEMPLOS\n" + rules.get("examples_guideline", ""))
    examples = rules.get("examples", [])
    for idx, example in enumerate(examples, start=1):
        prompt_sections.append(
            f"\n**EXEMPLO {idx}:**\nPai: \"{example.get('user', '')}\"\nSua Resposta (em JSON):\n\n"
            f"```json\n{json.dumps(example.get('model', {}), indent=2, ensure_ascii=False)}\n```\n"
        )
    return "".join(prompt_sections)


@dataclass
class AIResponse:
    reasoning: str
    messages: List[Dict[str, Any]]


class LouAIResponder:
    """Orchestrates Gemini calls and persists the AI replies via LouService."""

    def __init__(
        self,
        service: LouService,
        *,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.75,
    ) -> None:
        self._service = service
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._model_name = model_name
        self._temperature = temperature
        self._model_lock = threading.Lock()
        self._request_lock = threading.Lock()
        self._model: Any = None
        self._personality_signature: Optional[str] = None
        self._context_threads: set[threading.Thread] = set()
        self._recent_proactive_samples: Dict[str, Deque[Dict[str, str]]] = {}
        self._context_update_lock = threading.Lock()
        self._last_context_update_at = 0.0
        self._context_update_pending = 0
        self._context_update_interval = 180.0
        self._context_update_force_threshold = 4

    def _get_style_terms(self) -> List[str]:
        try:
            return self._service.get_allowed_slang_terms(limit=64)
        except Exception:
            return []

    def _call_model(
        self,
        model: Any,
        history: List[Dict[str, Any]],
        *,
        attempts: int = 1,
        allow_high_load_retry: bool = False,
        base_delay: float = 2.0,
    ) -> Any:
        last_error: Optional[Exception] = None
        for attempt in range(1, max(1, attempts) + 1):
            try:
                with self._request_lock:
                    return model.generate_content(history)
            except Exception as exc:  # pragma: no cover - network resilience
                should_retry = (
                    allow_high_load_retry
                    and attempt < attempts
                    and self._looks_like_high_load_error(exc)
                )
                if not should_retry:
                    raise
                last_error = exc
                sleep_for = base_delay * attempt
                time.sleep(max(0.5, sleep_for))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Falha ao gerar conteúdo com o modelo")

    def _looks_like_high_load_error(self, exc: Exception) -> bool:
        message = self._extract_error_message(exc)
        lowered = message.lower()
        keywords = (
            "high load",
            "overloaded",
            "busy",
            "try again",
            "resource exhausted",
            "quota",
            "429",
        )
        if any(keyword in lowered for keyword in keywords if keyword):
            return True
        status = getattr(exc, "code", None) or getattr(exc, "status", None) or getattr(exc, "status_code", None)
        return isinstance(status, int) and status in {429, 503}

    def _extract_error_message(self, exc: Exception) -> str:
        if exc is None:
            return ""
        if getattr(exc, "message", None):
            return str(exc.message)
        if exc.args:
            return " ".join(str(arg) for arg in exc.args if arg)
        return str(exc)

    def generate_reply(
        self,
        server_id: str,
        channel_id: str,
        *,
        reply_to: Optional[str] = None,
        media_context: Optional[Dict[str, Any]] = None,
    ) -> AIResponse:
        model = self._ensure_model()
        history = self._service.build_history_context(server_id, channel_id)
        if not history:
            raise ValueError("Historico insuficiente para gerar resposta")
        media_instruction = self._build_media_focus_instruction(media_context)
        if media_instruction:
            history.insert(2, {"role": "user", "parts": [media_instruction]})
        response = self._call_model(model, history)
        raw_text = self._extract_text(response)
        payload = self._parse_payload(raw_text)
        style_terms = self._get_style_terms()
        chunks = sanitize_and_split_response(payload.get("messages", ""), style_terms=style_terms)
        chunks = self._merge_incomplete_chunks(chunks)
        chunks = self._ensure_complete_chunks(chunks, history, model, style_terms)
        chunks = self._ensure_contextual_alignment(chunks, history, model, style_terms)
        if not chunks:
            raise RuntimeError("A IA retornou uma resposta vazia")
        created_messages: List[Dict[str, Any]] = []
        for index, chunk in enumerate(chunks):
            trimmed = chunk.strip()
            if not trimmed:
                continue
            attachments = []
            gif_payload = self._gif_attachment_from_chunk(trimmed)
            if gif_payload:
                attachments.append(gif_payload)
            create_payload = CreateMessagePayload(
                server_id=server_id,
                channel_id=channel_id,
                author_id="model",
                content=trimmed,
                reply_to=reply_to if index == 0 else None,
                attachments=attachments or None,
            )
            message = self._service.add_message(create_payload)
            created_messages.append(message)
        if not created_messages:
            raise RuntimeError("Nenhuma mensagem válida foi gerada pela IA")
        self._schedule_context_update(server_id, channel_id)
        return AIResponse(reasoning=payload.get("reasoning", ""), messages=created_messages)

    def _build_media_focus_instruction(self, media_context: Optional[Dict[str, Any]]) -> str:
        if not isinstance(media_context, dict):
            return ""
        if not media_context.get("isActive"):
            return ""
        if not media_context.get("enforce", True):
            return ""
        raw_title = str(media_context.get("title") or "").strip()
        title = raw_title.replace("\"", "'") if raw_title else "a transmissão atual"
        owner_mode = str(media_context.get("mode") or "").strip()
        owner_key = str(media_context.get("owner") or "").strip()
        is_ai_stream = owner_mode == "ai_stream" or owner_key == "ai"
        channel_name = str(media_context.get("channelName") or "").strip()
        channel_hint = f" no chat de voz '{channel_name}'" if channel_name else ""
        owner_name = str(media_context.get("ownerName") or "").strip()
        if not owner_name:
            owner_name = "Pai" if not is_ai_stream else "Lou"
        if is_ai_stream:
            return (
                f"[Contexto de Transmissão: Você está transmitindo ao vivo o vídeo \"{title}\"{channel_hint}. "
                "Descreva o que aparece na tela, reaja como apresentadora empolgada e mantenha o foco TOTAL nesse vídeo até a transmissão encerrar. "
                "Trate qualquer mensagem do Pai como comentário sobre essa transmissão.]"
            )
        return (
            f"[Contexto de Transmissão: {owner_name} está compartilhando agora o vídeo \"{title}\". "
            "Assista junto como espectadora, comente as cenas em tempo real, faça perguntas sobre o que estiver acontecendo na tela e não puxe outros assuntos até o compartilhamento terminar.]"
        )

    def _is_video_stream_context(self, media_context: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(media_context, dict):
            return False
        if not media_context.get("isActive"):
            return False
        mode = str(media_context.get("mode") or "").lower()
        owner = str(media_context.get("owner") or "").lower()
        return mode == "ai_stream" or owner == "ai"

    def generate_proactive_message(
        self,
        server_id: str,
        channel_id: str,
        *,
        attempt: int = 0,
        kind: str = "proactive",
        media_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        model = self._ensure_model()
        history = self._service.build_history_context(server_id, channel_id)
        if not history:
            raise ValueError("Historico insuficiente para mensagem proativa")
        media_instruction = self._build_media_focus_instruction(media_context)
        if media_instruction:
            insert_index = 2 if len(history) >= 2 else len(history)
            history.insert(insert_index, {"role": "user", "parts": [media_instruction]})
        self._maybe_seed_proactive_history(server_id, channel_id, history)
        normalized_kind = (kind or "proactive").strip().lower()
        is_video_stream = self._is_video_stream_context(media_context)
        if normalized_kind == "absence":
            prompt = VIDEO_ABSENCE_PROMPT if is_video_stream else PROACTIVE_CHECKIN_PROMPT
        elif normalized_kind == "video_swap":
            prompt = VIDEO_SWAP_PROMPT
        else:
            if is_video_stream:
                prompt = VIDEO_PROACTIVE_PROMPT
            else:
                prompt = PROACTIVE_CREATIVE_PROMPT if attempt < 2 else PROACTIVE_CHECKIN_PROMPT
        request_history = list(history)
        variation_instruction = self._build_proactive_variation_instruction(server_id, channel_id)
        if variation_instruction:
            request_history.append({"role": "user", "parts": [variation_instruction]})
        request_history.append({"role": "user", "parts": [prompt]})
        response = self._call_model(
            model,
            request_history,
            attempts=3,
            allow_high_load_retry=True,
            base_delay=2.5,
        )
        generated_text = (self._extract_text(response) or "").strip()
        payload = self._parse_payload(generated_text)
        candidate_text = payload.get("messages") or generated_text
        candidate_text = self._strip_code_fences(candidate_text)
        style_terms = self._get_style_terms()
        chunks = sanitize_and_split_response(candidate_text, style_terms=style_terms)
        chunks = self._merge_incomplete_chunks(chunks)
        sanitized_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        if not sanitized_chunks:
            sanitized_chunks = [candidate_text.strip()]
        primary_text = self._ensure_proactive_completion(
            sanitized_chunks[0],
            history,
            model,
            attempt,
            server_id,
            channel_id,
            style_terms,
            kind=normalized_kind,
            video_stream=is_video_stream,
        )
        sanitized_chunks[0] = primary_text.strip()
        created_messages: List[Dict[str, Any]] = []
        for chunk in sanitized_chunks:
            trimmed = chunk.strip()
            if not trimmed:
                continue
            payload = CreateMessagePayload(
                server_id=server_id,
                channel_id=channel_id,
                author_id="model",
                content=trimmed,
            )
            message = self._service.add_message(payload)
            created_messages.append(message)
        self._schedule_context_update(server_id, channel_id)
        return created_messages

    def _ensure_proactive_completion(
        self,
        text: str,
        history: List[Dict[str, Any]],
        model: Any,
        attempt: int,
        server_id: str,
        channel_id: str,
        style_terms: Optional[List[str]] = None,
        *,
        kind: str = "proactive",
        video_stream: bool = False,
    ) -> str:
        candidate = self._normalize_single_chunk(text, style_terms=style_terms)
        max_attempts = 3
        for round_index in range(max_attempts):
            if candidate and not self._needs_proactive_retry(
                candidate,
                history,
                server_id,
                channel_id,
                kind=kind,
                video_stream=video_stream,
            ):
                finalized = self._finalize_proactive_candidate(candidate, kind=kind)
                self._remember_proactive_candidate(server_id, channel_id, finalized)
                return finalized
            reason = self._diagnose_proactive_issue(
                candidate,
                history,
                server_id,
                channel_id,
                kind=kind,
                video_stream=video_stream,
            )
            candidate = self._normalize_single_chunk(
                self._request_proactive_fix(candidate, reason, history, model, attempt, round_index),
                style_terms=style_terms,
            )
        raise RuntimeError("Nao consegui gerar uma mensagem proativa completa a tempo")

    def _needs_proactive_retry(
        self,
        text: str,
        history: List[Dict[str, Any]],
        server_id: str,
        channel_id: str,
        *,
        kind: str = "proactive",
        video_stream: bool = False,
    ) -> bool:
        if not text.strip():
            return True
        if self._is_duplicate_of_recent_model(text, history):
            return True
        if self._is_similar_to_recent_proactive(text, server_id, channel_id):
            return True
        if re.search(r"(pensando aqui|lembr(ei|ando)|sabe o que)", text, re.IGNORECASE):
            return True
        if video_stream and kind in {"proactive", "absence", "video_swap"} and not self._references_video_context(text):
            return True
        if kind == "absence" and not self._looks_like_question(text):
            return True
        if kind == "video_swap" and not self._mentions_video_swap(text):
            return True
        return self._looks_incomplete_sentence(text)

    def _diagnose_proactive_issue(
        self,
        text: str,
        history: List[Dict[str, Any]],
        server_id: str,
        channel_id: str,
        *,
        kind: str = "proactive",
        video_stream: bool = False,
    ) -> str:
        if not text.strip():
            return "Mensagem vazia"
        if self._is_duplicate_of_recent_model(text, history):
            return "Você repetiu praticamente a mesma mensagem; tente outro ângulo"
        if self._is_similar_to_recent_proactive(text, server_id, channel_id):
            return "Você está usando o mesmo gancho das últimas proativas; mude a abertura e o foco"
        if re.search(r"(pensando aqui|lembr(ei|ando)|sabe o que)", text, re.IGNORECASE):
            return "Você começou um pensamento mas não concluiu"
        if video_stream and kind in {"proactive", "absence", "video_swap"} and not self._references_video_context(text):
            return "Você esqueceu de falar do que está acontecendo no vídeo ao vivo; traga a transmissão para o centro da frase"
        if kind == "absence" and not self._looks_like_question(text):
            return "Transforme em uma pergunta direta pra checar se ele ainda está assistindo"
        if kind == "video_swap" and not self._mentions_video_swap(text):
            return "Avise claramente que vai trocar o vídeo agora"
        if self._looks_incomplete_sentence(text):
            return "A frase terminou sem finalizar a ideia"
        return "Finalize a ideia com clareza"

    def _finalize_proactive_candidate(self, text: str, *, kind: str) -> str:
        normalized = text.strip()
        if kind == "absence" or ("?" not in normalized and self._looks_like_question(normalized)):
            normalized = self._ensure_question_format(normalized)
        return normalized

    def _references_video_context(self, text: str) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in VIDEO_CONTEXT_KEYWORDS)

    def _mentions_video_swap(self, text: str) -> bool:
        lowered = text.lower()
        return any(hint in lowered for hint in VIDEO_SWAP_HINTS)

    def _looks_like_question(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        if "?" in stripped:
            return True
        starters = (
            "oi",
            "cadê",
            "ta",
            "tá",
            "ainda",
            "sumiu",
            "segue",
            "voce",
            "você",
            "vocês",
            "voces",
            "vc",
            "cê",
            "ce",
            "que",
            "qual",
            "quais",
            "quando",
            "onde",
            "como",
            "sera",
            "será",
            "serao",
            "serão",
        )
        lowered = stripped.lower()
        tokens = [token.strip(",.!?…") for token in lowered.split() if token.strip(",.!?…")]
        if not tokens:
            return False
        if tokens[0] in starters:
            return True
        lead_ins = {"ai", "aí", "aii", "opa", "olha", "tipo", "eita", "aff", "oxe", "oxi", "ei"}
        if len(tokens) >= 2 and tokens[0] in lead_ins and tokens[1] in starters:
            return True
        suffixes = (
            " o que",
            " que call",
            " que é",
            " qual",
            " quais",
            " onde",
            " quando",
            " pra que",
            " por que",
        )
        base = lowered.rstrip(" ?")
        if any(base.endswith(suffix.strip()) for suffix in suffixes):
            return True
        mid_markers = (
            " o que ",
            " o que?",
            " o que vc",
            " o que voce",
            " o que você",
            " pra que ",
            " por que ",
            " sera que",
            " será que",
            " cadê você",
            " cadê voce",
            " cade você",
            " cade voce",
            " cadê vc",
            " cade vc",
            " tá aí",
            " ta ai",
            " tá por aí",
            " ta por ai",
        )
        if any(marker in lowered for marker in mid_markers):
            return True
        return False

    def _ensure_question_format(self, text: str) -> str:
        stripped = text.rstrip()
        if stripped.endswith("?"):
            return stripped
        stripped = stripped.rstrip(".!…")
        return f"{stripped}?"

    def _request_proactive_fix(
        self,
        previous_text: str,
        reason: str,
        history: List[Dict[str, Any]],
        model: Any,
        attempt: int,
        round_index: int,
    ) -> str:
        instruction = (
            "A mensagem proativa anterior ficou incorreta ({reason}). "
            "Você deve enviar UMA mensagem completa, natural, mencionando o sumiço do Pai e convidando" 
            " ele a responder. Não use 'pensando aqui' ou frases em aberto. Apenas conclua a ideia."
        ).format(reason=reason)
        if previous_text:
            instruction += f" Mensagem anterior: '{previous_text}'."
        if attempt >= 2:
            instruction += " Seja breve, como se estivesse checando se ele está por perto."
        else:
            instruction += " Traga um gancho leve relacionado com o último assunto ou algo novo."
        corrective_history = history + [{"role": "user", "parts": [instruction]}]
        response = self._call_model(
            model,
            corrective_history,
            attempts=3,
            allow_high_load_retry=True,
            base_delay=2.5,
        )
        return self._extract_text(response) or ""

    def _is_duplicate_of_recent_model(self, text: str, history: List[Dict[str, Any]], window: int = DUPLICATE_HISTORY_WINDOW) -> bool:
        fingerprint = self._message_fingerprint(text)
        if not fingerprint:
            return False
        recent: List[str] = []
        for entry in reversed(history):
            if entry.get("role") != "model":
                continue
            parts = entry.get("parts") or []
            if not parts:
                continue
            snippet = (parts[0] or "").strip()
            if not snippet or snippet.startswith("["):
                continue
            entry_fp = self._message_fingerprint(snippet)
            if not entry_fp:
                continue
            recent.append(entry_fp)
            if len(recent) >= window:
                break
        return fingerprint in recent

    def _message_fingerprint(self, text: str) -> str:
        if not text:
            return ""
        cleaned = self._strip_code_fences(text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        cleaned = re.sub(r"[\"'“”‘’]+", "", cleaned)
        cleaned = cleaned.strip(".?!…")
        if not cleaned:
            return ""
        return cleaned[:160]

    def _maybe_seed_proactive_history(
        self,
        server_id: str,
        channel_id: str,
        history: List[Dict[str, Any]],
    ) -> None:
        bucket = self._get_proactive_bucket(server_id, channel_id)
        if bucket:
            return
        seeded: List[Dict[str, str]] = []
        for entry in reversed(history):
            if entry.get("role") != "model":
                continue
            parts = entry.get("parts") or []
            if not parts:
                continue
            snippet = (parts[0] or "").strip()
            if not snippet or snippet.startswith("["):
                continue
            normalized = self._normalize_for_similarity(snippet)
            if not normalized:
                continue
            seeded.append({"raw": snippet, "normalized": normalized})
            if len(seeded) >= PROACTIVE_VARIATION_WINDOW:
                break
        for item in reversed(seeded):
            bucket.append(item)

    def _build_proactive_variation_instruction(self, server_id: str, channel_id: str) -> str:
        bucket = self._recent_proactive_samples.get(self._proactive_history_key(server_id, channel_id))
        if not bucket:
            return ""
        recent_entries = list(bucket)[-PROACTIVE_VARIATION_INSTRUCTION_LIMIT:]
        snippets = []
        for entry in recent_entries:
            raw = entry.get("raw", "").strip()
            snippet = self._shorten_for_prompt(raw)
            if snippet:
                snippets.append(snippet)
        if not snippets:
            return ""
        unique_snippets = list(dict.fromkeys(snippets))
        joined = " | ".join(f'"{snippet}"' for snippet in unique_snippets)
        return (
            "[Variedade Proativa: As últimas abordagens foram "
            f"{joined}. Traga agora um início e um gancho completamente diferentes, "
            "evitando repetir estruturas como 'Pai, será que...'.]"
        )

    def _shorten_for_prompt(self, text: str, limit: int = 90) -> str:
        trimmed = (text or "").strip()
        if not trimmed:
            return ""
        single_line = re.sub(r"\s+", " ", trimmed)
        if len(single_line) > limit:
            return single_line[: limit - 1].rstrip() + "…"
        return single_line

    def _proactive_history_key(self, server_id: str, channel_id: str) -> str:
        return f"{server_id}:{channel_id}"

    def _get_proactive_bucket(self, server_id: str, channel_id: str) -> Deque[Dict[str, str]]:
        key = self._proactive_history_key(server_id, channel_id)
        bucket = self._recent_proactive_samples.get(key)
        if bucket is None:
            bucket = deque(maxlen=PROACTIVE_VARIATION_WINDOW)
            self._recent_proactive_samples[key] = bucket
        return bucket

    def _remember_proactive_candidate(self, server_id: str, channel_id: str, text: str) -> None:
        normalized = self._normalize_for_similarity(text)
        if not normalized:
            return
        bucket = self._get_proactive_bucket(server_id, channel_id)
        bucket.append({"raw": text.strip(), "normalized": normalized})

    def _normalize_for_similarity(self, text: str) -> str:
        cleaned = self._strip_code_fences(text or "")
        cleaned = cleaned.lower()
        cleaned = re.sub(r"https?://\S+", " ", cleaned)
        cleaned = re.sub(r"[^0-9a-záéíóúâêîôûãõàèìòùç\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def _is_similar_to_recent_proactive(
        self,
        text: str,
        server_id: str,
        channel_id: str,
        threshold: float = PROACTIVE_SIMILARITY_THRESHOLD,
    ) -> bool:
        normalized = self._normalize_for_similarity(text)
        if not normalized:
            return False
        bucket = self._recent_proactive_samples.get(self._proactive_history_key(server_id, channel_id))
        if not bucket:
            return False
        for entry in bucket:
            existing = entry.get("normalized")
            if not existing:
                continue
            similarity = SequenceMatcher(None, normalized, existing).ratio()
            if similarity >= threshold:
                return True
        return False

    def _normalize_single_chunk(self, text: str, style_terms: Optional[List[str]] = None) -> str:
        cleaned = self._strip_code_fences(text or "")
        chunks = sanitize_and_split_response(cleaned, style_terms=style_terms)
        for chunk in chunks:
            trimmed = chunk.strip()
            if trimmed:
                return trimmed
        return cleaned.strip()

    def _merge_incomplete_chunks(self, chunks: List[str]) -> List[str]:
        if not chunks:
            return []
        merged: List[str] = []
        buffer = ""
        for chunk in chunks:
            candidate = chunk if not buffer else f"{buffer} {chunk}".strip()
            if self._looks_incomplete_sentence(candidate):
                buffer = candidate
                continue
            merged.append(candidate)
            buffer = ""
        if buffer:
            if merged:
                merged[-1] = f"{merged[-1]} {buffer}".strip()
            else:
                merged.append(buffer)
        return merged

    def _ensure_complete_chunks(
        self,
        chunks: List[str],
        history: List[Dict[str, Any]],
        model: Any,
        style_terms: Optional[List[str]] = None,
    ) -> List[str]:
        if not chunks:
            return []
        if not self._looks_incomplete_sentence(chunks[-1]):
            return chunks
        fragment = chunks[-1].strip()
        corrective_prompt = (
            "A última resposta que você enviou terminou incompleta nesta frase: '{fragment}'. "
            "Continue SOMENTE a partir desse ponto e finalize o raciocínio em até duas frases curtas."
        ).format(fragment=fragment)
        corrective_history = history + [{"role": "user", "parts": [corrective_prompt]}]
        response = self._call_model(model, corrective_history)
        addition_text = self._strip_code_fences(self._extract_text(response) or "")
        addition_chunks = sanitize_and_split_response(addition_text, style_terms=style_terms)
        addition_chunks = self._merge_incomplete_chunks(addition_chunks)
        if not addition_chunks:
            chunks[-1] = fragment.rstrip(",") + "..."
            return chunks
        chunks[-1] = f"{fragment} {addition_chunks[0]}".strip()
        if len(addition_chunks) > 1:
            chunks.extend(addition_chunks[1:])
        if self._looks_incomplete_sentence(chunks[-1]):
            chunks[-1] = chunks[-1].rstrip(",") + "..."
        return chunks

    def _ensure_contextual_alignment(
        self,
        chunks: List[str],
        history: List[Dict[str, Any]],
        model: Any,
        style_terms: Optional[List[str]] = None,
    ) -> List[str]:
        if not chunks:
            return []
        user_context = self._collect_recent_user_text(history)
        if not user_context.strip():
            return chunks
        combined = " ".join(chunks)
        if not self._needs_contextual_fix(combined, user_context):
            return chunks
        attempts = 2
        for attempt in range(attempts):
            corrective_text = self._request_on_topic_fix(combined, user_context, history, model, attempt)
            cleaned = self._strip_code_fences(corrective_text or "")
            sanitized = sanitize_and_split_response(cleaned, style_terms=style_terms)
            sanitized = self._merge_incomplete_chunks(sanitized)
            if not sanitized:
                continue
            candidate = " ".join(sanitized)
            if not self._needs_contextual_fix(candidate, user_context):
                return sanitized
            combined = candidate
        return chunks

    def _collect_recent_user_text(self, history: List[Dict[str, Any]], limit: int = 6) -> str:
        user_lines: List[str] = []
        for entry in history:
            if entry.get("role") != "user":
                continue
            parts = entry.get("parts") or []
            if not parts:
                continue
            snippet = (parts[0] or "").strip()
            if not snippet or snippet.startswith("["):
                continue
            user_lines.append(snippet)
        if not user_lines:
            return ""
        return " ".join(user_lines[-limit:])

    def _needs_contextual_fix(self, candidate: str, user_context: str) -> bool:
        if not candidate:
            return False
        if not self._detect_creation_pitch(candidate):
            return False
        return not self._detect_creation_pitch(user_context)

    def _detect_creation_pitch(self, text: str) -> bool:
        lowered = (text or "").lower()
        if not lowered:
            return False
        has_verb = any(verb in lowered for verb in CREATION_VERBS)
        if not has_verb:
            return False
        has_topic = any(topic in lowered for topic in PROJECT_TOPICS)
        return has_topic

    def _request_on_topic_fix(
        self,
        previous_text: str,
        user_context: str,
        history: List[Dict[str, Any]],
        model: Any,
        attempt: int,
    ) -> str:
        instruction = (
            "Sua resposta anterior saiu do assunto porque sugeriu criar algo novo (jogo/app/projeto) sem o Pai pedir. "
            "Reescreva tudo mantendo o foco APENAS no que o Pai falou recentemente."
        )
        if user_context.strip():
            instruction += f" Baseie-se nessas falas recentes do Pai: '{user_context.strip()}'."
        instruction += f" Resposta anterior: '{previous_text.strip()}'."
        instruction += " Entregue no máximo duas frases curtas, naturais e zero propostas inéditas."
        if attempt:
            instruction += " Desta vez, confirme explicitamente algo que o Pai disse antes de mudar de assunto."
        corrective_history = history + [{"role": "user", "parts": [instruction]}]
        response = self._call_model(model, corrective_history)
        return self._extract_text(response) or previous_text

    def _looks_incomplete_sentence(self, text: str) -> bool:
        stripped = (text or "").strip()
        if not stripped:
            return True
        if stripped[-1] in ".!?":
            return False
        lower = stripped.lower()
        if lower.endswith("...") or lower.endswith("…"):
            return True
        if lower.endswith(","):
            return True
        if len(stripped) <= 6: 
            tokens = stripped.split()
            if len(tokens) >= 2:
                return False
            return True
        for suffix in INCOMPLETE_SUFFIXES:
            if lower.endswith(suffix):
                return True
        return False


    def _schedule_context_update(self, server_id: str, channel_id: str) -> None:
        snippet_all, snippet_user, structured_dialog = self._build_conversation_snippets(server_id, channel_id)
        if not snippet_all:
            return
        if not self._should_run_context_update():
            return
        snapshot = self._service.get_context_snapshot()
        def _runner() -> None:
            try:
                self._context_update_thread(snippet_all, snippet_user, structured_dialog, snapshot)
            finally:
                self._context_threads.discard(threading.current_thread())
        thread = threading.Thread(target=_runner, name="LouContextWorker", daemon=True)
        self._context_threads.add(thread)
        thread.start()

    def _should_run_context_update(self) -> bool:
        now = time.time()
        with self._context_update_lock:
            self._context_update_pending += 1
            cooldown_active = (now - self._last_context_update_at) < self._context_update_interval
            under_force_threshold = self._context_update_pending < self._context_update_force_threshold
            if cooldown_active and under_force_threshold:
                return False
            self._context_update_pending = 0
            self._last_context_update_at = now
            return True

    def _context_update_thread(
        self,
        snippet_all: str,
        snippet_user: str,
        structured_dialog: List[Dict[str, str]],
        snapshot: Dict[str, List[str]],
    ) -> None:
        try:
            profiles = self._service.get_profiles()
            user_name = profiles.get("user", {}).get("name", "Pai")
            model = self._ensure_model()
            prompt = self._build_context_prompt(snippet_all, snippet_user, snapshot, user_name)
            response = self._call_model(model, [{"role": "user", "parts": [prompt]}])
            raw = (self._extract_text(response) or "").strip()
            if not raw:
                return
            data = self._parse_context_response(raw)
            if not data:
                return
            
            # Gera short_term determinístico direto do histórico para evitar autores incorretos
            short_term_entries = self._build_short_term_history(structured_dialog, user_name)
            self._service.overwrite_short_term_memories(short_term_entries)
            
            # Processa styles independentemente de short_term
            # Styles captura APENAS padrões de escrita/gírias do usuário
            if data.get("styles") and self._service.allow_style_autolearn():
                if snippet_user.strip():
                    filtered_styles = self._filter_style_entries(
                        data["styles"], user_name, snippet_user, snippet_all
                    )
                    if filtered_styles:
                        self._service.save_styles(filtered_styles)
        except Exception as exc:  # pragma: no cover - background safety
            print(f"[LouAIResponder] Falha ao atualizar contexto: {exc}")

    def _build_conversation_snippets(self, server_id: str, channel_id: str) -> Tuple[str, str, List[Dict[str, str]]]:
        messages = self._service.list_messages(server_id, channel_id)
        profiles = self._service.get_profiles()
        user_name = profiles.get("user", {}).get("name", "Pai")
        model_name = profiles.get("model", {}).get("name", "Lou")
        relevant = messages[-12:]
        if not relevant:
            return "", "", []
        lines: List[str] = []
        user_lines: List[str] = []
        structured: List[Dict[str, str]] = []
        for item in relevant:
            author_token = item.get("author_id") or item.get("authorId")
            author = model_name if author_token == "model" else user_name
            content = item.get("content", "").strip()
            if content:
                lines.append(f"{author}: {content}")
                if author == user_name:
                    user_lines.append(f"{author}: {content}")
                structured.append({"author": author, "content": content})
        return "\n".join(lines[-10:]), "\n".join(user_lines[-10:]), structured[-20:]

    def _build_context_prompt(
        self,
        snippet_all: str,
        snippet_user: str,
        snapshot: Dict[str, List[str]],
        user_name: str,
    ) -> str:
        short_term = json.dumps(snapshot.get("short_term", []), ensure_ascii=False)
        styles = json.dumps(snapshot.get("styles", []), ensure_ascii=False)
        return (
            "Você é o módulo de memórias e estilos da Lou.\n\n"
            "## MEMÓRIAS DE CURTO PRAZO ##\n"
            "Analise TODAS as falas do diálogo (tanto do Pai quanto da Lou) e crie resumos narrativos"
            " de cada mensagem na ordem em que aparecem. Isso serve como contexto do que aconteceu"
            " nas últimas 20 mensagens do chat.\n\n"
            "**REGRAS CRÍTICAS DE IDENTIFICAÇÃO:**\n"
            f"- Se a linha começa com 'Lou:', então LOU falou → resumo deve começar com 'Lou ...'\n"
            f"- Se a linha começa com '{user_name}:' ou 'Pai:', então O PAI falou → resumo deve começar com '{user_name} ...'\n"
            "- NUNCA troque os autores! Verifique o prefixo de cada linha antes de resumir.\n"
            "- Não copie diálogos literais. Faça resumos factuais de cada mensagem.\n"
            "- Capture fatos, decisões, sentimentos, perguntas e respostas.\n"
            "- Liste no máximo 6 memórias novas por rodada.\n\n"
            "## PADRÕES DE ESTILO ##\n"
            "**ATENÇÃO:** Analise SOMENTE as falas que começam com '{user_name}:' ou 'Pai:'.\n"
            "IGNORE completamente as falas que começam com 'Lou:' (essas são da IA).\n\n"
            "Identifique gírias, abreviações e formas únicas de escrita que O PAI usa:\n"
            "- Exemplos: abreviações ('vc', 'tb', 'pq'), risadas ('kkk', 'hehe'),"
            " repetições de letras ('looou', 'simmmm'), gírias ('daora', 'sussa'), etc.\n"
            "- Descreva cada padrão: 'Abrevia X para Y', 'Usa X como forma de Y'.\n"
            "- NÃO liste padrões que já existem na lista atual.\n"
            "- NÃO liste padrões das falas da Lou.\n"
            "- Se não houver falas do Pai, retorne styles vazio [].\n\n"
            "Histórico completo recente:\n"
            f"---\n{snippet_all}\n---\n\n"
            f"Falas APENAS do Pai (linhas que começam com '{user_name}:' ou 'Pai:'):\n"
            f"---\n{snippet_user or 'Sem falas recentes do Pai'}\n---\n\n"
            f"Memórias curtas atuais: {short_term}\n"
            f"Padrões de estilo atuais: {styles}\n\n"
            "Responda SOMENTE com um JSON:\n"
            "{\"short_term\": [\"memoria1\", \"memoria2\"], \"styles\": [\"padrao1\", \"padrao2\"]}\n\n"
            "Exemplos CORRETOS:\n"
            "Histórico: 'Lou: Oi! Tudo bem?' → short_term: ['Lou cumprimenta e pergunta se está tudo bem']\n"
            f"Histórico: '{user_name}: Oi tb' → short_term: ['{user_name} retorna o cumprimento'], styles: ['Usa \"tb\" como abreviação de \"também\"']\n"
            f"Histórico: 'Lou: Vou bem, e vc?' → short_term: ['Lou diz que está bem e pergunta sobre {user_name}'], styles: [] (VAZIO porque Lou falou, não o Pai)\n\n"
            "Liste apenas itens novos; se não houver mudanças, retorne {}."
        )

    def _build_short_term_history(
        self,
        conversation: List[Dict[str, str]],
        user_name: str,
        limit: int = 20,
    ) -> List[str]:
        if not conversation:
            return []
        summaries: List[str] = []
        for entry in conversation[-limit:]:
            author = entry.get("author", "").strip()
            content = entry.get("content", "")
            summary = self._summarize_dialog_message(author, content, user_name)
            if summary:
                summaries.append(summary)
        return summaries[-limit:]

    def _summarize_dialog_message(self, author: str, text: str, user_name: str) -> Optional[str]:
        content = (text or "").strip()
        if not author or not content:
            return None
        normalized = re.sub(r"\s+", " ", content)
        if not normalized:
            return None
        if len(normalized) > 160:
            normalized = normalized[:157].rstrip() + "…"
        upper = normalized.upper()
        if upper.startswith("GIF:"):
            slug = normalized[4:].strip() or "animado"
            return f"{author} envia o GIF '{slug}'"
        verb = "pergunta" if normalized.endswith("?") else "exclama" if normalized.endswith("!") else "comenta"
        return f"{author} {verb}: {normalized}"

    def _parse_context_response(self, text: str) -> Dict[str, List[str]]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        json_blob = text[start : end + 1]
        try:
            data = json.loads(json_blob)
        except json.JSONDecodeError:
            return {}
        parsed: Dict[str, List[str]] = {}
        if isinstance(data.get("short_term"), list):
            parsed["short_term"] = [str(item).strip() for item in data["short_term"] if str(item).strip()]
        if isinstance(data.get("styles"), list):
            parsed["styles"] = [str(item).strip() for item in data["styles"] if str(item).strip()]
        return parsed

    def _filter_style_entries(
        self,
        entries: List[str],
        user_name: str,
        snippet_user: str,
        snippet_all: str,
    ) -> List[str]:
        """Filtra padrões de estilo garantindo que vêm exclusivamente das falas do usuário."""

        if not snippet_user.strip():
            return []

        filtered: List[str] = []
        user_aliases = {user_name.lower(), "pai"}
        user_lines: List[str] = []

        for raw_line in (snippet_all or "").splitlines():
            if ":" not in raw_line:
                continue
            speaker, _, content = raw_line.partition(":")
            if speaker.strip().lower() in user_aliases:
                user_lines.append(content.strip().lower())

        if not user_lines:
            return []

        for entry in entries:
            normalized = (entry or "").strip()
            if not normalized:
                continue

            lower = normalized.lower()
            if any(term in lower for term in ["lou", "ia", "modelo", "assistente", "bot", "model"]):
                continue

            quoted_terms = re.findall(r"['\"]([^'\"]+)['\"]", normalized)
            if not quoted_terms:
                continue

            term_from_user = True
            valid_style_terms = 0
            for term in quoted_terms:
                term_lower = term.lower().strip()
                if not any(term_lower in user_line for user_line in user_lines):
                    term_from_user = False
                    break
                if self._looks_like_style_snippet(term):
                    valid_style_terms += 1

            if not term_from_user:
                continue

            if not valid_style_terms:
                continue

            filtered.append(normalized)

        return filtered

    def _looks_like_style_snippet(self, term: str) -> bool:
        normalized = re.sub(r"\s+", " ", (term or "").strip().lower())
        if not normalized:
            return False
        tokens = [token for token in re.split(r"[\s,]+", normalized) if token]
        if not tokens:
            return False
        core_tokens = [token for token in tokens if token not in STYLE_TERM_CONNECTORS]
        if not core_tokens:
            return False
        if len(core_tokens) > 3:
            return False
        if len(tokens) == 1:
            return True
        return self._contains_style_marker(tokens)

    def _contains_style_marker(self, tokens: List[str]) -> bool:
        return any(self._looks_like_style_word(token) for token in tokens)

    def _looks_like_style_word(self, token: str) -> bool:
        cleaned = re.sub(r"[^0-9a-záéíóúâêîôûãõàèìòùç]+", "", (token or "").lower())
        if not cleaned:
            return False
        if cleaned in STYLE_KEYWORD_TOKENS:
            return True
        if any(char in STYLE_ACCENT_CHARS for char in cleaned):
            return True
        if re.search(r"(.)\1{1,}", cleaned):
            return True
        if any(cleaned.endswith(suffix) for suffix in STYLE_EMPHASIS_SUFFIXES):
            return True
        return len(cleaned) <= 3

    def _maybe_rebalance_short_term(
        self,
        entries: List[str],
        snippet_all: str,
        user_name: str,
        model: Any,
        snapshot: Dict[str, List[str]],
    ) -> List[str]:
        normalized = self._normalize_short_term_entries(entries)
        validated = self._validate_short_term_entries(normalized, snippet_all, user_name)
        if validated:
            ordered = self._deduplicate_preserve_order(validated, limit=20)
            if ordered:
                return ordered
        regenerated = self._regenerate_short_term_entries(model, snippet_all, snapshot, user_name)
        regenerated = self._normalize_short_term_entries(regenerated)
        if not regenerated:
            return []
        revalidated = self._validate_short_term_entries(regenerated, snippet_all, user_name)
        return self._deduplicate_preserve_order(revalidated, limit=20)

    def _regenerate_short_term_entries(
        self,
        model: Any,
        snippet_all: str,
        snapshot: Dict[str, List[str]],
        user_name: str,
    ) -> Optional[List[str]]:
        prompt = (
            "ERRO DETECTADO: Você atribuiu memórias aos autores errados.\n\n"
            "REGRAS CRÍTICAS:\n"
            f"1. Se a linha começa com 'Lou:', então LOU falou → use 'Lou ...' no resumo\n"
            f"2. Se a linha começa com '{user_name}:' ou 'Pai:', então {user_name.upper()} falou → use '{user_name} ...' no resumo\n"
            "3. NUNCA troque os autores!\n"
            "4. Verifique CUIDADOSAMENTE o prefixo de cada linha antes de criar o resumo.\n\n"
            f"Gere NOVAMENTE apenas o campo short_term com as atribuições CORRETAS.\n"
            "Produza no máximo 6 frases curtas e únicas.\n"
            "Responda somente com JSON: {{\"short_term\": [...]}}."
        )
        full_prompt = (
            f"{prompt}\n\nHistórico recente:\n---\n{snippet_all}\n---\n\n"
            f"Memórias atuais (INCORRETAS): {json.dumps(snapshot.get('short_term', []), ensure_ascii=False)}"
        )
        response = self._call_model(model, [{"role": "user", "parts": [full_prompt]}])
        raw = (self._extract_text(response) or "").strip()
        parsed = self._parse_context_response(raw)
        if parsed.get("short_term"):
            return [entry.strip() for entry in parsed["short_term"] if entry.strip()]
        return None

    def _normalize_short_term_entries(self, entries: Optional[List[str]]) -> List[str]:
        normalized: List[str] = []
        if not entries:
            return normalized
        for entry in entries:
            text = (entry or "").strip().rstrip(".")
            if not text:
                continue
            if text and text[0].islower():
                text = text[0].upper() + text[1:]
            normalized.append(text)
        return normalized

    def _validate_short_term_entries(
        self,
        entries: List[str],
        snippet_all: str,
        user_name: str,
    ) -> List[str]:
        """
        Valida se as memórias de curto prazo estão atribuindo corretamente os autores.
        VALIDAÇÃO RIGOROSA: Verifica se cada memória corresponde corretamente ao autor da fala.
        """
        if not entries:
            return []
        
        lower_entries = [entry.lower() for entry in entries]
        has_lou_dialog = "Lou:" in snippet_all or "lou:" in snippet_all.lower()
        has_user_dialog = (f"{user_name}:" in snippet_all) or ("Pai:" in snippet_all)
        
        # Se há diálogos de Lou mas nenhuma memória menciona Lou, algo está errado
        if has_lou_dialog and not any("lou" in entry for entry in lower_entries):
            return []
        
        user_aliases = {user_name.lower(), "pai"}
        
        # Se há diálogos do usuário mas nenhuma memória o menciona, algo está errado
        if has_user_dialog and not any(any(alias in entry for alias in user_aliases) for entry in lower_entries):
            return []
        
        # Prepara mapeamento linha-por-linha do histórico para validação precisa
        actor_tokens = self._prepare_actor_token_sets(snippet_all, user_name)
        
        # Valida cada entrada individualmente
        for entry in entries:
            expected_actor = self._extract_entry_actor(entry, user_aliases)
            if not expected_actor:
                # Entrada não começa com um nome válido (Lou ou user_name)
                return []
            
            # Infere quem deveria ser o autor baseado nos tokens da fala
            inferred_actor = self._infer_actor_from_tokens(entry, actor_tokens)
            
            # Se conseguimos inferir o autor e ele não bate com o esperado, REJEITA TUDO
            if inferred_actor and inferred_actor != expected_actor:
                return []
        
        return entries

    def _extract_entry_actor(self, entry: str, user_aliases: Set[str]) -> Optional[str]:
        normalized = (entry or "").strip().lower()
        if normalized.startswith("lou "):
            return "lou"
        for alias in user_aliases:
            if normalized.startswith(f"{alias} "):
                return "user"
        return None

    def _prepare_actor_token_sets(self, snippet_all: str, user_name: str) -> List[Tuple[str, Set[str]]]:
        actor_tokens: List[Tuple[str, Set[str]]] = []
        if not snippet_all.strip():
            return actor_tokens
        user_aliases = {user_name.lower(), "pai"}
        for raw_line in snippet_all.splitlines():
            if ":" not in raw_line:
                continue
            speaker, _, text = raw_line.partition(":")
            speaker_key = speaker.strip().lower()
            if speaker_key == "lou":
                actor = "lou"
            elif speaker_key in user_aliases:
                actor = "user"
            else:
                continue
            tokens = self._tokenize_text(text)
            if tokens:
                actor_tokens.append((actor, tokens))
        return actor_tokens

    def _infer_actor_from_tokens(self, entry: str, actor_tokens: List[Tuple[str, Set[str]]]) -> Optional[str]:
        if not actor_tokens:
            return None
        entry_tokens = self._tokenize_text(entry)
        if not entry_tokens:
            return None
        best_actor: Optional[str] = None
        best_score = 0
        for actor, tokens in actor_tokens:
            score = len(entry_tokens.intersection(tokens))
            if score > best_score:
                best_actor = actor
                best_score = score
        if best_score >= 2:
            return best_actor
        return None

    def _tokenize_text(self, text: str) -> Set[str]:
        if not text:
            return set()
        return {match.group(0).lower() for match in re.finditer(r"[a-zá-úç0-9']{3,}", text.lower())}

    def _deduplicate_preserve_order(self, entries: List[str], limit: Optional[int] = None) -> List[str]:
        seen = set()
        ordered: List[str] = []
        for entry in entries:
            normalized = entry.strip()
            if not normalized or normalized in seen:
                continue
            ordered.append(normalized)
            seen.add(normalized)
            if limit and len(ordered) >= limit:
                break
        return ordered

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _ensure_model(self) -> Any:
        if genai is None:
            raise RuntimeError("Instale o pacote 'google-generativeai' para ativar a IA")
        if not self._api_key:
            raise RuntimeError("Defina a variável de ambiente GEMINI_API_KEY para ativar a IA no Neve")
        personality = self._service.get_personality_prompt() or {}
        signature = json.dumps(personality, sort_keys=True)
        with self._model_lock:
            if self._model is None or signature != self._personality_signature:
                genai.configure(api_key=self._api_key)
                system_instruction = build_system_instruction(personality)
                self._model = genai.GenerativeModel(
                    self._model_name,
                    system_instruction=system_instruction,
                    generation_config={"temperature": self._temperature},
                )
                self._personality_signature = signature
        return self._model

    def _extract_text(self, response: Any) -> str:
        if response is None:
            return ""
        text = getattr(response, "text", "") or ""
        if text:
            return text
        candidates = getattr(response, "candidates", None)
        if not candidates:
            return ""
        snippets: List[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", None)
            if not parts:
                continue
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    snippets.append(part_text)
        return "\n".join(snippets)

    def _parse_payload(self, raw_text: str) -> Dict[str, Any]:
        text = (raw_text or "").strip()
        if not text:
            return {"reasoning": "", "messages": ""}
        text = self._strip_code_fences(text)
        json_blob = self._extract_json_blob(text)
        if json_blob:
            try:
                data = json.loads(json_blob)
                reasoning = self._strip_code_fences(str(data.get("reasoning", "")))
                messages = self._strip_code_fences(str(data.get("messages", "")))
                return {
                    "reasoning": reasoning,
                    "messages": messages,
                }
            except json.JSONDecodeError:
                pass
        return {"reasoning": "", "messages": text}

    def _extract_json_blob(self, text: str) -> Optional[str]:
        fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, flags=re.IGNORECASE)
        if fenced:
            return fenced.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start : end + 1]

    def _strip_code_fences(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r"```(?:json)?\s*([\s\S]*?)```", r"\1", text, flags=re.IGNORECASE).strip()

    def _gif_attachment_from_chunk(self, chunk: str) -> Optional[Dict[str, str]]:
        if not chunk.upper().startswith("GIF:"):
            return None
        _, _, remainder = chunk.partition(":")
        slug = remainder.strip().split()[0] if remainder.strip() else ""
        if not slug:
            return None
        filename = self._resolve_gif_filename(slug)
        if not filename:
            return None
        return {"type": "gif", "name": slug, "filename": filename}

    def _resolve_gif_filename(self, slug: str) -> Optional[str]:
        normalized = slug.strip().lower()
        gifs_dir = self._service.config.gifs_dir
        for gif_path in gifs_dir.glob("*.gif"):
            if gif_path.stem.lower() == normalized:
                return gif_path.name
        return None


__all__ = ["LouAIResponder", "AIResponse", "build_system_instruction"]
