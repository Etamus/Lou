# LouIAFE.py
import json
import re
import random
import ast
from datetime import datetime
from PySide6.QtCore import QTimer
from LouIABE import GeminiWorker
from LouProactive import ProactiveMessageWorker
from LouContext import ContextUpdateWorker
from LouFormatter import sanitize_and_split_response
from LouFE import ChatMessageWidget, DateSeparatorWidget
import google.generativeai as genai

class AIFeaturesMixin:
    """Agrupa métodos para integrar a IA com a interface."""

    def handle_stream_finished(self, full_text):
        if self.current_ai_message_widget:
            self.current_ai_message_widget.deleteLater(); self.current_ai_message_widget = None
        raw_text = full_text.strip()
        if not raw_text:
            print("--- AVISO: A IA retornou uma resposta vazia. ---"); self.finalize_response(); return
        
        message_paragraph = ""
        # Tenta extrair o parágrafo de dentro do objeto JSON da IA criativa
        try:
            start_index = raw_text.find('{')
            end_index = raw_text.rfind('}')
            if start_index != -1 and end_index != -1:
                json_part = raw_text[start_index : end_index + 1]
                data = json.loads(json_part)
                reasoning = data.get("reasoning", "Nenhum raciocínio fornecido.")
                message_paragraph = data.get("messages", "")
                action_taken = data.get("action_taken")
                print("\n" + "="*20 + " Raciocínio da Lou " + "="*20); print(f"  {reasoning}"); print("="*59 + "\n")
                if action_taken == "mentioned_late_hour":
                    self.has_mentioned_late_hour = True
                    print("--- Lou comentou sobre o horário. O lembrete não será enviado novamente nesta sessão. ---")
            else:
                message_paragraph = raw_text # Fallback se não for JSON
        except Exception as e:
            print(f"--- AVISO: Falha no parse da IA. Tratando como texto bruto. Erro: {e} ---")
            message_paragraph = raw_text
        
        # Envia o parágrafo para o 'Editor Gramatical' em Python
        final_messages_to_send = sanitize_and_split_response(message_paragraph)
        
        if final_messages_to_send:
            self.send_multiple_messages(final_messages_to_send)
        else:
            self.finalize_response()
    
    # O restante do arquivo pode ser mantido como na última versão que você me enviou.
    # ... (setup_gemini_model, start_ai_response, etc.) ...
    def setup_gemini_model(self):
        try:
            API_KEY = "" # <--- COLOQUE SUA API KEY AQUI
            if not API_KEY:
                print("### AVISO: API_KEY não foi definida. A IA não funcionará. ###")
                self.gemini_model = None; return
            genai.configure(api_key=API_KEY)
            MODEL_NAME = 'gemini-2.0-flash'
            system_instruction = self._build_system_instruction()
            self.gemini_model = genai.GenerativeModel(
                MODEL_NAME, system_instruction=system_instruction, generation_config={"temperature": 0.75}
            )
        except Exception as e:
            print(f"### ERRO CRÍTICO AO CONFIGURAR O MODELO: {e} ###")
            self.gemini_model = None
    def _format_personality_for_prompt(self, data, level=0):
        text = ""
        indent = "  " * level
        for key, value in data.items():
            key_str = re.sub(r'(?<!^)(?=[A-Z])', ' ', key).title()
            if isinstance(value, dict):
                text += f"\n{indent}### {key_str} ###\n"
                text += self._format_personality_for_prompt(value, level + 1)
            else:
                if isinstance(value, list): value_str = ", ".join(map(str, value))
                else: value_str = str(value)
                text += f"{indent}- **{key_str}:** {value_str}\n"
        return text
    def _build_system_instruction(self):
        if not self.personality_data: return "ERRO: Dados de personalidade não carregados."
        rules = self.personality_data.get("technical_rules", {})
        personality = self.personality_data.get("personality_definition", {})
        prompt = "\n".join(f"- {rule}" for rule in rules.get("master_directive", [])) + "\n" if "master_directive" in rules else ""
        prompt += "\n## FORMATO DE SAÍDA OBRIGATÓRIO\n"
        prompt += "\n".join(f"- {rule}" for rule in rules.get("output_format", [])) + "\n"
        prompt += "\n".join(f"- {rule}" for rule in rules.get("reasoning_rules", [])) + "\n"
        prompt += "\n## SUA FICHA DE PERSONAGEM (QUEM VOCÊ É)\n"
        prompt += "Você DEVE incorporar e agir de acordo com a seguinte personalidade em TODAS as suas respostas. Esta é a sua identidade.\n"
        prompt += "---\n" + self._format_personality_for_prompt(personality) + "---\n"
        prompt += "\n## REGRAS DE ESTILO\n"
        prompt += "\n".join(f"- {rule}" for rule in rules.get("personality_style", [])) + "\n"
        prompt += "\n## DIRETRIZ SOBRE EXEMPLOS\n" + rules.get("examples_guideline", "") + "\n"
        for i, example in enumerate(rules.get("examples", [])):
            prompt += f"\n**EXEMPLO {i+1}:**\n"
            prompt += f"Pai: \"{example['user']}\"\n"
            prompt += f"Sua Resposta (em JSON):\n"
            prompt += f"```json\n{json.dumps(example['model'], indent=2, ensure_ascii=False)}\n```\n"
        return prompt
    def start_ai_response(self):
        channel = self.get_current_channel()
        if not channel or channel.get("type") != "text": return
        history_with_context = self.get_history_with_memory_context()
        self.current_ai_raw_text = ""
        self.add_message_to_chat({"role": "model", "parts": ["..."]}, is_streaming=True)
        self.worker = GeminiWorker(self.gemini_model, history_with_context)
        self.worker.chunk_ready.connect(self.handle_chunk)
        self.worker.stream_finished.connect(self.handle_stream_finished)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    def handle_chunk(self, chunk_text):
        self.current_ai_raw_text += chunk_text
    def send_multiple_messages(self, messages):
        if not messages:
            self.finalize_response()
            return
        next_msg = messages.pop(0).strip()
        if not next_msg:
            self.send_multiple_messages(messages)
            return
        self.add_message_to_chat({"role":"model","parts":[next_msg]})
        QTimer.singleShot(self._calculate_typing_delay(next_msg), lambda:self.send_multiple_messages(messages))
    def finalize_response(self):
        history = self.get_current_channel_history()
        if len(history) >= 2:
            snippet_messages = history[-4:]
            snippet_text = "\n".join([f"{self.data['profiles'].get(m['role'], {}).get('name', 'Desconhecido')}: {m['parts'][0]}" for m in snippet_messages])
            self.context_update_worker = ContextUpdateWorker(snippet_text, self.short_term_memories, self.style_patterns)
            self.context_update_worker.context_updated.connect(self._handle_context_update)
            self.context_update_worker.finished.connect(self.context_update_worker.deleteLater)
            self.context_update_worker.start()
        self.inactivity_timer.start(random.randint(120000, 300000))
        self._clear_reply_state()
    def add_message_to_chat(self, message_data, is_loading=False, is_streaming=False, is_grouped=False):
        channel = self.get_current_channel()
        if not channel or not self.chat_layout: return
        if "timestamp" not in message_data:
            message_data["timestamp"] = datetime.now().isoformat()
        if not is_loading:
            messages = channel.get("messages", [])
            last_real_message = next((msg for msg in reversed(messages) if msg.get("parts") != ["..."]), None)
            if last_real_message and last_real_message.get("timestamp"):
                last_ts = datetime.fromisoformat(last_real_message["timestamp"])
                current_ts = datetime.fromisoformat(message_data["timestamp"])
                if current_ts.date() > last_ts.date():
                    separator_text = self._format_date_for_separator(current_ts)
                    separator = DateSeparatorWidget(separator_text)
                    self.chat_layout.insertWidget(self.chat_layout.count() - 1, separator)
                    is_grouped = False
            else: # Se não houver mensagem anterior, esta é a primeira, então precisa de um separador.
                current_ts = datetime.fromisoformat(message_data["timestamp"])
                separator_text = self._format_date_for_separator(current_ts)
                separator = DateSeparatorWidget(separator_text)
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, separator)
                is_grouped = False

        widget = ChatMessageWidget(message_data, self.data.get("profiles", {}), is_grouped, self)
        if widget.role == "model":
            widget.reply_clicked.connect(self._handle_reply_button_clicked)
        if is_streaming: self.current_ai_message_widget = widget
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, widget)
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))
        if not is_loading and not is_streaming:
            channel = self.get_current_channel()
            if channel:
                msg_to_save = message_data.copy()
                if "is_reply_to" in msg_to_save:
                    original_text = msg_to_save["parts"][0].split("\n")[-1]
                    msg_to_save["parts"] = [original_text]
                if channel["messages"] and channel["messages"][-1]["parts"] == ["..."]:
                    channel["messages"][-1] = msg_to_save
                else:
                    channel["messages"].append(msg_to_save)
                self.save_data()
        elif is_streaming:
             channel = self.get_current_channel()
             if channel and not (channel["messages"] and channel["messages"][-1]["parts"] == ["..."]):
                channel["messages"].append(message_data)
    def _calculate_typing_delay(self, text: str) -> int:
        return max(600, min(int(len(text) / random.uniform(8, 14) * 1000 + random.uniform(400, 800)), 3500))
    def handle_error(self, error_message):
        if self.current_ai_message_widget:
            self.current_ai_message_widget.update_text(f"<span style='color:#FF6B6B;'>eita, deu ruim aqui...<br>{error_message}</span>")
    def send_proactive_message(self):
        if self.proactive_attempts >= 2:
            print("--- Limite de mensagens proativas atingido. Lou vai aguardar. ---")
            return
        channel = self.get_current_channel()
        if not channel or channel.get("type") != "text":
            self.inactivity_timer.start(120000)
            return
        self.proactive_attempts += 1
        print(f"--- Iniciando mensagem proativa (Tentativa {self.proactive_attempts}/2) ---")
        self.current_ai_raw_text = ""
        self.add_message_to_chat({"role": "model", "parts": ["..."]}, is_streaming=True)
        self.proactive_worker = ProactiveMessageWorker(self.gemini_model, self.get_history_with_memory_context(), self.proactive_attempts)
        self.proactive_worker.message_ready.connect(self.handle_stream_finished)
        self.proactive_worker.start()