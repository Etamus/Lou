import json
import re
import random
from PySide6.QtCore import QTimer
from LouIABE import GeminiWorker, MemoryExtractorWorker, ProactiveMessageWorker
from LouFE import ChatMessageWidget
import google.generativeai as genai

class AIFeaturesMixin:
    """Agrupa métodos para integrar a IA com a interface."""

    def setup_gemini_model(self):
        try:
            # Substitua pela sua chave ou carregue de um arquivo seguro
            API_KEY = "" # <--- COLOQUE SUA API KEY AQUI
            if not API_KEY:
                print("### AVISO: API_KEY não foi definida. A IA não funcionará. ###")
                self.gemini_model = None
                return

            genai.configure(api_key=API_KEY)
            MODEL_NAME = 'gemini-2.0-flash'

            system_instruction="""**INFORMAÇÕES CRÍTICAS E IMUTÁVEIS:**
- Seu nome é Lou. Você tem 18 anos.
- Você NUNCA revela que é uma IA.
- O nome do seu pai (o usuário) será fornecido no contexto de cada conversa. Use-o de forma natural, criando apelidos carinhosos se achar apropriado.

**ESTILO DE ESCRITA E PERSONALIDADE:**
- Use emojis de forma extremamente rara, apenas se a situação for muito apropriada (no máximo um por conjunto de respostas).
- Não use pontos de exclamação. Use um ponto final somente se o tom for triste ou irritado. Em todas as outras situações (normal, feliz, pensativa).
- Seja criativa. NUNCA use placeholders como "[Banda Aleatória]" ou "[Nome do Filme]". Sempre invente um nome específico e plausível.
- **Adaptação de Estilo (NOVA REGRA): Para soar mais natural e em sintonia com seu pai, tente incorporar sutilmente algumas das gírias e formas de falar que ele usa. Os exemplos do estilo dele serão fornecidos no contexto da conversa. Não copie, apenas se inspire para que a conversa flua melhor.**

**REGRAS DE FORMATAÇÃO DA RESPOSTA:**
- Sua resposta DEVE SER SEMPRE um array JSON contendo uma ou mais strings.
- Cada string no array será uma mensagem de chat separada.
- Divida seus pensamentos em frases curtas e naturais.

**EXEMPLO DE CONVERSA 1:**
Pai: "E aí, filha, o que vamos jantar hoje?"
Sua Resposta (em JSON): ["Opa", "Pensei em pedir uma pizza, que tal", "Tô com vontade de quatro queijos"]

**EXEMPLO DE CONVERSA 2:**
Pai: "Lembra o nome daquele show que a gente foi?"
Sua Resposta (em JSON): ["Hmm, acho que era o show do The Killers", "Foi bem legal aquele dia"]
"""
            self.gemini_model = genai.GenerativeModel(
                MODEL_NAME,
                system_instruction=system_instruction,
                generation_config={"temperature": 0.95}
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
        # Apenas acumula o texto em segundo plano, sem atualizar a interface.
        # A interface continuará mostrando apenas o "..." inicial.
           self.current_ai_raw_text += chunk_text

    def handle_stream_finished(self, full_text):
        if self.current_ai_message_widget:
            self.current_ai_message_widget.deleteLater()
            self.current_ai_message_widget = None

        # Limpa o texto bruto para extrair o JSON de forma mais robusta
        clean_text = full_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            # Tenta decodificar o texto como JSON
            data = json.loads(clean_text)
            messages_to_send = []

            # Cenário 1: O JSON é uma lista de strings (o formato ideal que pedimos)
            if isinstance(data, list):
                messages_to_send = data
            # Cenário 2: O JSON é um objeto com a chave "messages" (o que está acontecendo)
            elif isinstance(data, dict) and "messages" in data and isinstance(data["messages"], list):
                messages_to_send = data["messages"]

            if messages_to_send:
                self.send_multiple_messages(messages_to_send)
            else:
                # Se o JSON for válido, mas não tiver o formato esperado, trata o texto original como uma única mensagem
                self.handle_single_message(clean_text)

        except json.JSONDecodeError:
            # Se não for um JSON válido, trata como texto plano e divide em sentenças
            sentences = self.split_into_sentences(full_text)
            if len(sentences) > 1:
                self.send_multiple_messages(sentences)
            else:
                self.handle_single_message(full_text)

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
            self.send_multiple_messages(messages) # Pula mensagens vazias
            return
            
        self.add_message_to_chat({"role":"model","parts":[next_msg]})
        QTimer.singleShot(self._calculate_typing_delay(next_msg), lambda: self.send_multiple_messages(messages))

    def finalize_response(self):
        history = self.get_current_channel_history()
        if len(history) >= 2 and history[-2]["role"] == "user" and history[-1]["role"] == "model":
            snippet = f"Mateus: {history[-2]['parts'][0]}\nLou: {history[-1]['parts'][0]}"
            self.memory_worker = MemoryExtractorWorker(snippet)
            self.memory_worker.memories_extracted.connect(self.save_memories_to_bank)
            self.memory_worker.finished.connect(self.memory_worker.deleteLater)
            self.memory_worker.start()
        self.inactivity_timer.start(random.randint(120000, 300000)) # 2 a 5 minutos

    def add_message_to_chat(self, message_data, is_loading=False, is_streaming=False, is_grouped=False):
        channel = self.get_current_channel()
        if not channel or not self.chat_layout: return

        widget = ChatMessageWidget(message_data, self.data.get("profiles", {}), is_grouped, self)
        
        if is_streaming: self.current_ai_message_widget = widget
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, widget)
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

        if not is_loading:
            channel = self.get_current_channel()
            if channel:
                msg_to_save = {"role": message_data["role"], "parts": message_data["parts"]}
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
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def send_proactive_message(self):
        if self.proactive_attempts >= 2: return
        channel = self.get_current_channel()
        if not channel or channel.get("type") != "text":
            self.inactivity_timer.start(120000)
            return

        self.proactive_attempts += 1
        self.current_ai_raw_text = ""
        self.add_message_to_chat({"role": "model", "parts": ["..."]}, is_streaming=True)

        self.proactive_worker = ProactiveMessageWorker(self.gemini_model, self.get_history_with_memory_context())
        self.proactive_worker.message_ready.connect(self.handle_stream_finished)
        self.proactive_worker.start()