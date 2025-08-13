# LouIAFE.py
import json
import re
import random
import ast
from datetime import datetime
from PySide6.QtCore import QTimer
from LouIABE import GeminiWorker, ProactiveMessageWorker, ContextUpdateWorker
from LouFE import ChatMessageWidget, DateSeparatorWidget
import google.generativeai as genai

class AIFeaturesMixin:
    """Agrupa métodos para integrar a IA com a interface."""

    def _format_personality_for_prompt(self, personality_data):
        """Converte o JSON de personalidade em um texto legível para a IA."""
        if not personality_data:
            return "Personalidade padrão: Amigável e prestativa."

        text = ""
        for category, details in personality_data.items():
            text += f"\n## {category.replace('_', ' ').upper()}\n"
            for key, value in details.items():
                if isinstance(value, list):
                    value_str = ", ".join(map(str, value))
                else:
                    value_str = str(value)
                # Formata a chave para ser mais legível (ex: NomeCompleto -> Nome Completo)
                key_str = re.sub(r'(?<!^)(?=[A-Z])', ' ', key).title()
                text += f"- **{key_str}:** {value_str}\n"
        return text

    def _build_system_instruction(self):
        """Constrói o system prompt completo a partir do arquivo de personalidade."""
        if not self.personality_data:
            return "ERRO: Dados de personalidade não carregados."

        rules = self.personality_data.get("technical_rules", {})
        personality = self.personality_data.get("personality_definition", {})

        prompt = "## FORMATO DE SAÍDA OBRIGATÓRIO\n"
        # Atualizado para incluir a chave opcional 'action_taken'
        prompt += "- Sua resposta DEVE ser um único objeto JSON contendo a chave 'messages' e, opcionalmente, as chaves 'reasoning' e 'action_taken'.\n"
        prompt += "- A chave 'reasoning' DEVE conter uma string explicando brevemente quais traços da sua personalidade influenciaram a resposta.\n"
        prompt += "- A chave 'messages' DEVE conter um array de uma ou mais strings, que serão as mensagens exibidas no chat.\n"
        prompt += "- Se você realizar uma ação especial solicitada no contexto (como mencionar o horário), a chave 'action_taken' DEVE conter uma string descrevendo a ação (ex: 'mentioned_late_hour').\n"
        
        prompt += "\n".join(f"- {rule}" for rule in rules.get("output_format_rules", [])) + "\n"
        
        prompt += "\n## SUA FICHA DE PERSONAGEM (QUEM VOCÊ É)\n"
        prompt += "Você DEVE incorporar e agir de acordo com a seguinte personalidade em TODAS as suas respostas. Esta é a sua identidade.\n"
        prompt += "---"
        prompt += self._format_personality_for_prompt(personality)
        prompt += "---\n"

        prompt += "\n## DIRETRIZ SOBRE EXEMPLOS\n"
        prompt += rules.get("examples_guideline", "") + "\n"
        
        for i, example in enumerate(rules.get("examples", [])):
            prompt += f"\n**EXEMPLO {i+1}:**\n"
            prompt += f"Pai: \"{example['user']}\"\n"
            prompt += f"Sua Resposta (em JSON):\n"
            prompt += f"```json\n{json.dumps(example['model'], indent=2, ensure_ascii=False)}\n```\n"
            
        return prompt

    def setup_gemini_model(self):
        try:
            API_KEY = "AIzaSyBY9kbNA6gXX3H39hS4KVxR7XAa3ouGt1k" # <--- COLOQUE SUA API KEY AQUI
            if not API_KEY:
                print("### AVISO: API_KEY não foi definida. A IA não funcionará. ###")
                self.gemini_model = None
                return

            genai.configure(api_key=API_KEY)
            MODEL_NAME = 'gemini-2.0-flash'

            # Constrói o prompt dinamicamente
            system_instruction = self._build_system_instruction()
            
            # Se você quiser ver o prompt completo que está sendo enviado para a IA, descomente a linha abaixo
            # print(system_instruction)

            self.gemini_model = genai.GenerativeModel(
                MODEL_NAME,
                system_instruction=system_instruction,
                generation_config={"temperature": 0.9}
            )
        except Exception as e:
            print(f"### ERRO CRÍTICO AO CONFIGURAR O MODELO: {e} ###")
            self.gemini_model = None

    # O restante do arquivo LouIAFE.py continua exatamente o mesmo...
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
    def handle_stream_finished(self, full_text):
        if self.current_ai_message_widget:
            self.current_ai_message_widget.deleteLater()
            self.current_ai_message_widget = None

        clean_text = full_text.strip()
        if not clean_text:
            print("--- AVISO: A IA retornou uma resposta vazia. ---")
            return

        start_index = clean_text.find('{')
        end_index = clean_text.rfind('}')
        if start_index != -1 and end_index != -1:
            clean_text = clean_text[start_index : end_index + 1]
        
        try:
            data = json.loads(clean_text)
            
            reasoning = data.get("reasoning", "Nenhum raciocínio fornecido.")
            messages_to_send = data.get("messages", [])
            action_taken = data.get("action_taken") # <-- Pega a ação

            print("\n" + "="*20 + " Raciocínio da Lou " + "="*20)
            print(f"  {reasoning}")
            print("="*59 + "\n")

            # --- ATUALIZA O ESTADO SE A AÇÃO FOI REALIZADA ---
            if action_taken == "mentioned_late_hour":
                self.has_mentioned_late_hour = True
                print("--- Lou comentou sobre o horário. O lembrete não será enviado novamente nesta sessão. ---")

            if messages_to_send and isinstance(messages_to_send, list):
                self.send_multiple_messages(messages_to_send)
            else:
                self.finalize_response()

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"--- AVISO: Falha no parse da resposta da IA. Tratando como texto plano. Erro: {e} ---")
            print(f"Resposta Bruta: {full_text}")
            self.send_multiple_messages([full_text])
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
        if '\n' in next_msg:
            parts = [part.strip() for part in next_msg.split('\n') if part.strip()]
            if parts:
                next_msg = parts.pop(0)
                if parts:
                    messages.insert(0, *parts)
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
# Em LouIAFE.py, substitua este método

    def add_message_to_chat(self, message_data, is_loading=False, is_streaming=False, is_grouped=False):
        channel = self.get_current_channel()
        if not channel or not self.chat_layout: return

        if "timestamp" not in message_data:
            message_data["timestamp"] = datetime.now().isoformat()

        # --- NOVA LÓGICA DE VERIFICAÇÃO DE DATA EM TEMPO REAL ---
        if not is_loading:
            messages = channel.get("messages", [])
            # Pega a última mensagem real no histórico (ignora o "...")
            last_real_message = next((msg for msg in reversed(messages) if msg.get("parts") != ["..."]), None)

            if last_real_message and last_real_message.get("timestamp"):
                last_ts = datetime.fromisoformat(last_real_message["timestamp"])
                current_ts = datetime.fromisoformat(message_data["timestamp"])

                # Se a data mudou, insere um separador
                if current_ts.date() > last_ts.date():
                    separator_text = self._format_date_for_separator(current_ts)
                    separator = DateSeparatorWidget(separator_text)
                    self.chat_layout.insertWidget(self.chat_layout.count() - 1, separator)
                    is_grouped = False # Força a nova mensagem a não ser agrupada

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