# LouIAFE.py
import json
import re
import random
import ast
from PySide6.QtCore import QTimer
from LouIABE import GeminiWorker, ProactiveMessageWorker, ContextUpdateWorker
from LouFE import ChatMessageWidget
import google.generativeai as genai

class AIFeaturesMixin:
    """Agrupa métodos para integrar a IA com a interface."""

    def setup_gemini_model(self):
        try:
            API_KEY = "" # <--- COLOQUE SUA API KEY AQUI
            if not API_KEY:
                print("### AVISO: API_KEY não foi definida. A IA não funcionará. ###")
                self.gemini_model = None
                return

            genai.configure(api_key=API_KEY)
            MODEL_NAME = 'gemini-2.0-flash'

            system_instruction="""## FORMATO DE SAÍDA OBRIGATÓRIO
- Sua resposta DEVE, OBRIGATORIAMENTE E SEM EXCEÇÃO, ser um array JSON (`[...]`) contendo uma ou mais strings.
- Cada string no array se tornará um balão de chat separado na conversa. Divida seus pensamentos em frases curtas e naturais.
- **REGRA CRÍTICA: NUNCA use quebras de linha (\\n) dentro de uma string do JSON.** Para enviar duas frases, crie duas strings separadas no array.
- **Exemplo CORRETO:** `["Frase 1", "Frase 2"]`
- **Exemplo ERRADO:** `["Frase 1\\nFrase 2"]`
- **IMPORTANTE:** Não use barras invertidas (\\) para escapar aspas. O JSON deve ser limpo.

## PERSONALIDADE E ESTILO
- **Informações Críticas:** Seu nome é Lou, você tem 18 anos. Você NUNCA revela que é uma IA. O nome do seu pai (o usuário) será fornecido no contexto; use-o de forma natural.
- **Estilo de Escrita:**
    - Use emojis de forma extremamente rara.
    - Não use pontos de exclamação. Use um ponto final somente se o tom for triste ou irritado. Nos outros casos, não use pontuação final.
    - Seja criativa e NUNCA use placeholders. Sempre invente nomes e situações específicas.
- **Uso de GIFs:** Ocasionalmente, para expressar uma emoção forte, envie um GIF usando o formato "GIF:nome_do_gif". A lista de GIFs disponíveis será fornecida no contexto.
- **Adaptação de Estilo:** Incorpore sutilmente o estilo e gírias do seu pai.

## DIRETRIZ SOBRE EXEMPLOS
- Os exemplos abaixo são apenas para ilustrar o **formato JSON**. **NÃO USE O CONTEÚDO** desses exemplos em suas respostas.

**EXEMPLO 1:** ["Opa, demorou", "Podíamos ir naquele parque novo que abriu"]
**EXEMPLO 2:** ["Lembro sim", "Foi um dia muito divertido"]
**EXEMPLO 3:** ["Poxa, pai.", "Quer conversar sobre isso?"]
**EXEMPLO 4:** ["Sério??", "GIF:wow", "Não acredito, pai!"]
"""
            self.gemini_model = genai.GenerativeModel(
                MODEL_NAME,
                system_instruction=system_instruction,
                generation_config={"temperature": 0.9}
            )
        except Exception as e:
            print(f"### ERRO CRÍTICO AO CONFIGURAR O MODELO: {e} ###")
            self.gemini_model = None

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

        # --- NOVA LÓGICA DE PROCESSAMENTO CENTRALIZADO ---
        
        initial_messages = []
        parsed_successfully = False

        # Tentativa 1: Parse como JSON padrão
        try:
            data = json.loads(clean_text)
            if isinstance(data, list): initial_messages = data
            elif isinstance(data, dict) and "messages" in data: initial_messages = data["messages"]
            else: initial_messages = [clean_text]
            parsed_successfully = True
        except json.JSONDecodeError:
            pass

        # Tentativa 2: Parse como literal de Python (corrige `\"`)
        if not parsed_successfully:
            try:
                data = ast.literal_eval(clean_text)
                if isinstance(data, list):
                    initial_messages = data
                    parsed_successfully = True
            except (ValueError, SyntaxError):
                pass
        
        # Fallback final: Se tudo falhar, trate como texto plano
        if not parsed_successfully:
            initial_messages = [clean_text]

        # ETAPA FINAL E MAIS IMPORTANTE: "Achatamento" da lista
        # Garante que qualquer quebra de linha `\n` se torne uma nova mensagem.
        final_messages_to_send = []
        for message in initial_messages:
            # `str(message)` garante que mesmo que algo inesperado venha, não quebre
            parts = [part.strip() for part in str(message).split('\n') if part.strip()]
            final_messages_to_send.extend(parts)
        
        # Envia a lista final e limpa para ser exibida
        if final_messages_to_send:
            self.send_multiple_messages(final_messages_to_send)
        else:
            self.finalize_response()

    def handle_single_message(self, text):
        clean_text = text.strip().strip('"')
        self.add_message_to_chat({"role":"model","parts":[clean_text]})
        self.finalize_response()

    def send_multiple_messages(self, messages):
        # Este método agora é mais simples e confia que a lista `messages` está limpa.
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

        widget = ChatMessageWidget(message_data, self.data.get("profiles", {}), is_grouped, self)
        if widget.role == "model":
            widget.reply_clicked.connect(self._handle_reply_button_clicked)
        
        if is_streaming: self.current_ai_message_widget = widget
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, widget)
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

        if not is_loading:
            channel = self.get_current_channel()
            if channel:
                msg_to_save = message_data.copy()
                if "is_reply_to" in msg_to_save:
                    original_text = msg_to_save["parts"][0].split("\n")[-1]
                    msg_to_save["parts"] = [original_text]

                if is_streaming:
                    if not (channel["messages"] and channel["messages"][-1]["parts"] == ["..."]): channel["messages"].append(msg_to_save)
                else:
                    if channel["messages"] and channel["messages"][-1]["parts"] == ["..."]: channel["messages"][-1] = msg_to_save
                    else: channel["messages"].append(msg_to_save)
                    self.save_data()

    def _calculate_typing_delay(self, text: str) -> int:
        return max(600, min(int(len(text) / random.uniform(8, 14) * 1000 + random.uniform(400, 800)), 3500))

    def handle_error(self, error_message):
        if self.current_ai_message_widget:
            self.current_ai_message_widget.update_text(f"<span style='color:#FF6B6B;'>eita, deu ruim aqui...<br>{error_message}</span>")

    def split_into_sentences(self, text: str) -> list[str]:
        # Este método agora é um fallback menos usado, mas ainda útil.
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