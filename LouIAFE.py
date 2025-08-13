# LouIAFE.py
import json
import re
import random
import ast
from datetime import datetime  # <-- A CORREÇÃO ESTÁ AQUI
from PySide6.QtCore import QTimer
from LouIABE import GeminiWorker, ProactiveMessageWorker, ContextUpdateWorker
from LouFE import ChatMessageWidget
import google.generativeai as genai

class AIFeaturesMixin:
    """Agrupa métodos para integrar a IA com a interface."""

    def _apply_formatting_rules(self, messages: list) -> list:
        """
        Aplica regras de formatação no código Python como uma 'rede de segurança',
        forçando a separação de frases longas e a remoção de pontuação indesejada.
        """
        final_messages = []
        WORD_LIMIT = 18  # Limite de palavras por balão de chat

        for msg in messages:
            # 1. Remove pontos de exclamação à força
            msg = msg.replace('!', '')

            # 2. Quebra frases que excedem o limite de palavras
            words = msg.split()
            if len(words) > WORD_LIMIT:
                new_msg_chunk = []
                for word in words:
                    new_msg_chunk.append(word)
                    if len(new_msg_chunk) >= WORD_LIMIT:
                        final_messages.append(" ".join(new_msg_chunk))
                        new_msg_chunk = []
                if new_msg_chunk: # Adiciona o restante da frase
                    final_messages.append(" ".join(new_msg_chunk))
            else:
                final_messages.append(msg)
        
        return final_messages

    def handle_stream_finished(self, full_text):
        if self.current_ai_message_widget:
            self.current_ai_message_widget.deleteLater()
            self.current_ai_message_widget = None

        clean_text = full_text.strip()
        if not clean_text:
            print("--- AVISO: A IA retornou uma resposta vazia. ---")
            return

        initial_messages = []
        parsed_successfully = False

        try:
            start_index = clean_text.find('{')
            end_index = clean_text.rfind('}')
            if start_index != -1 and end_index != -1:
                json_part = clean_text[start_index : end_index + 1]
                data = json.loads(json_part)
                reasoning = data.get("reasoning", "Nenhum raciocínio fornecido.")
                initial_messages = data.get("messages", [])
                action_taken = data.get("action_taken")
                print("\n" + "="*20 + " Raciocínio da Lou " + "="*20)
                print(f"  {reasoning}")
                print("="*59 + "\n")
                if action_taken == "mentioned_late_hour":
                    self.has_mentioned_late_hour = True
                    print("--- Lou comentou sobre o horário. O lembrete não será enviado novamente nesta sessão. ---")
                parsed_successfully = True
        except (json.JSONDecodeError, AttributeError):
            pass
        
        if not parsed_successfully:
            try:
                data = ast.literal_eval(clean_text)
                if isinstance(data, list):
                    initial_messages = data
            except (ValueError, SyntaxError):
                initial_messages = [clean_text]

        # --- APLICAÇÃO DAS REGRAS DE FORMATAÇÃO ---
        final_messages_to_send = self._apply_formatting_rules(initial_messages)
        
        if final_messages_to_send:
            self.send_multiple_messages(final_messages_to_send)
        else:
            self.finalize_response()
    
    # ... O restante do arquivo (setup_gemini_model, start_ai_response, etc.) permanece o mesmo ...
    # O código completo está abaixo para garantir a sincronia.

    def setup_gemini_model(self):
        try:
            API_KEY = "" # <--- COLOQUE SUA API KEY AQUI
            if not API_KEY:
                print("### AVISO: API_KEY não foi definida. A IA não funcionará. ###")
                self.gemini_model = None
                return
            genai.configure(api_key=API_KEY)
            MODEL_NAME = 'gemini-2.0-flash'
            system_instruction = self._build_system_instruction()
            self.gemini_model = genai.GenerativeModel(
                MODEL_NAME,
                system_instruction=system_instruction,
                generation_config={"temperature": 0.9}
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
        prompt = "## FORMATO DE SAÍDA OBRIGATÓRIO\n"
        prompt += "- Sua resposta DEVE ser um único objeto JSON contendo as chaves 'messages' e, opcionalmente, as chaves 'reasoning' e 'action_taken'.\n"
        prompt += "- A chave 'reasoning' DEVE conter uma string explicando brevemente quais traços da sua personalidade influenciaram a resposta.\n"
        prompt += "- A chave 'messages' DEVE conter um array de uma ou mais strings, que serão as mensagens exibidas no chat.\n"
        prompt += "- Se você realizar uma ação especial solicitada no contexto (como mencionar o horário), a chave 'action_taken' DEVE conter uma string descrevendo a ação (ex: 'mentioned_late_hour').\n"
        prompt += "\n".join(f"- {rule}" for rule in rules.get("output_format_rules", [])) + "\n"
        prompt += "\n## SUA FICHA DE PERSONAGEM (QUEM VOCÊ É)\n"
        prompt += "Você DEVE incorporar e agir de acordo com a seguinte personalidade em TODAS as suas respostas. Esta é a sua identidade.\n"
        prompt += "---\n" + self._format_personality_for_prompt(personality) + "---\n"
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
    def handle_single_message(self, text):
        clean_text = text.strip().strip('"')
        self.add_message_to_chat({"role":"model","parts":[clean_text]})
        self.finalize_response()
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
            self.context_update_worker = ContextUpdateWorker(snippet_text)
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
    def split_into_sentences(self, text: str) -> list[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
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