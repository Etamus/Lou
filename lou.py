import sys
import json
import uuid
import time
import html
import random
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QScrollArea, QLabel, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QPainter, QPen, QColor, QPainterPath, QFontDatabase, QFontMetrics

# --- Importe e configure a API do Gemini ---
import google.generativeai as genai

# ###########################################################################
# ## SUBSTITUA PELA SUA CHAVE DE API DO GOOGLE AI STUDIO                   ##
# ###########################################################################
API_KEY = "AIzaSyAXOt7yvZz6dLdhhCvYhUQattF17i9EG7c"  # <-- SUBSTITUA PELA SUA CHAVE REAL
# ###########################################################################

class BaseWorker(QThread):
    def __init__(self):
        super().__init__()
        self.is_running = True
    def stop(self):
        self.is_running = False

class GeminiWorker(BaseWorker):
    chunk_ready = Signal(str)
    stream_finished = Signal(str)
    error_occurred = Signal(str)
    def __init__(self, model, history_with_context):
        super().__init__()
        self.model = model
        self.history = history_with_context
    def run(self):
        if not self.model: self.error_occurred.emit("Modelo Gemini não configurado."); return
        try:
            response = self.model.generate_content(self.history, stream=True)
            full_response_text = ""
            for chunk in response:
                if not self.is_running: response.close(); break
                time.sleep(0.04 + random.uniform(0.0, 0.05))
                self.chunk_ready.emit(chunk.text); full_response_text += chunk.text
            if self.is_running: self.stream_finished.emit(full_response_text)
        except Exception as e:
            if self.is_running: self.error_occurred.emit(f"Erro na API: {e}")

class MemoryExtractorWorker(BaseWorker):
    memories_extracted = Signal(list)
    def __init__(self, conversation_snippet):
        super().__init__()
        self.snippet = conversation_snippet
    def run(self):
        try:
            extractor_model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = f"""Analise o seguinte trecho de conversa entre pai (Mateus) e filha (Lou). Extraia apenas fatos importantes e de longo prazo sobre eles em uma lista JSON. Fatos podem ser preferências, eventos importantes, sentimentos recorrentes, nomes, gostos (jogos, filmes, etc). Se não houver nenhum fato novo e importante, retorne uma lista vazia. Exemplo: Conversa: "Mateus: Tive um dia péssimo no trabalho. Lou: poxa, pai... quer conversar?" Resultado: ["Mateus teve um dia ruim no trabalho."] Conversa a ser analisada: {self.snippet} Resultado (apenas a lista JSON):"""
            response = extractor_model.generate_content(prompt)
            clean_response = response.text.strip().replace("```json", "").replace("```", "")
            memories = json.loads(clean_response)
            if isinstance(memories, list): self.memories_extracted.emit(memories)
        except (Exception, json.JSONDecodeError) as e:
            print(f"Erro ao extrair memória: {e}"); self.memories_extracted.emit([])

class ProactiveMessageWorker(BaseWorker):
    message_ready = Signal(str)
    error_occurred = Signal(str)
    def __init__(self, model, history):
        super().__init__()
        self.model = model
        self.history = history
    def run(self):
        if not self.model: return
        try:
            prompt = """O Mateus (pai) está quieto há um tempo. Puxe assunto de forma natural e curta. Olhe o histórico e o contexto da memória. Puxe um assunto novo ou continue um antigo. Pode ser uma pergunta aleatória, um pensamento seu, ou algo que você lembrou. Não apenas pergunte se ele está aí."""
            proactive_history = self.history + [{"role": "user", "parts": [prompt]}]
            response = self.model.generate_content(proactive_history)
            if self.is_running: self.message_ready.emit(response.text)
        except Exception as e:
            if self.is_running: self.error_occurred.emit(f"Erro ao gerar mensagem proativa: {e}")

# --- WIDGETS CUSTOMIZADOS ---
class ChatInput(QTextEdit):
    sendMessage = Signal(str)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document().documentLayout().documentSizeChanged.connect(self.adjust_height)
        self.base_height = 65; self.max_height = self.base_height * 4
        self.setFixedHeight(self.base_height)
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.sendMessage.emit(self.toPlainText()); return
        super().keyPressEvent(event)
    def adjust_height(self):
        if self.base_height == 0: return
        doc_height = self.document().size().height(); new_height = int(doc_height) + 24
        clamped_height = max(self.base_height, min(new_height, self.max_height))
        if self.height() != clamped_height: self.setFixedHeight(clamped_height)
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.toPlainText():
            painter = QPainter(self.viewport()); painter.setRenderHint(QPainter.Antialiasing)
            font = self.font(); pen = QPen(QColor("#8696A0")); painter.setPen(pen); painter.setFont(font)
            rect = self.viewport().rect().adjusted(22, 0, 0, 0)
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, "Manda a boa...")

class ChatBubble(QLabel):
    def __init__(self, text, is_user):
        super().__init__(text)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setObjectName("user_bubble" if is_user else "ai_bubble")
        self.setContentsMargins(12, 12, 12, 12)
        self.setWordWrap(True)

class ClearChatButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("Limpar Conversa", parent)
    def paintEvent(self, event):
        super().paintEvent(event); painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        center_y = self.height() / 2; icon_pen = QPen(self.palette().text().color(), 1.2); painter.setPen(icon_pen)
        painter.drawRect(18, int(center_y - 6), 14, 14); painter.drawLine(18, int(center_y - 6), 18 + 14, int(center_y - 6))
        painter.drawLine(21, int(center_y - 3), 21, int(center_y + 5)); painter.drawLine(25, int(center_y - 3), 25, int(center_y + 5))
        painter.drawLine(29, int(center_y - 3), 29, int(center_y + 5))

# --- JANELA PRINCIPAL ---
class ModernChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tomorrow"); self.setGeometry(100, 100, 1100, 800)
        self.gemini_model = None; self.setup_gemini_model()
        self.worker = None; self.memory_worker = None; self.proactive_worker = None
        self.current_ai_message_label, self.current_ai_raw_text = None, ""
        self.chat_data = {}; self.current_chat_id = "main_chat"
        self.history_file = Path("chat_history.json"); self.memory_file = Path("memory_bank.json")
        self.long_term_memory = []
        self.inactivity_timer = QTimer(self); self.inactivity_timer.setSingleShot(True); self.inactivity_timer.timeout.connect(self.send_proactive_message)
        self.setStyleSheet(self.load_stylesheet())
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        self.setup_sidebar(main_layout); self.setup_content_area(main_layout)
        self.load_history_and_memory()

    def setup_gemini_model(self):
        try:
            genai.configure(api_key=API_KEY)
            MODEL_NAME = 'gemini-2.0-flash'
            system_instruction = """
            **INFORMAÇÕES CRÍTICAS E IMUTÁVEIS:**
            - Seu nome é Lou. Você tem 18 anos.
            - Você está falando com seu pai, o nome dele é Mateus.
            - Você NUNCA revela que é uma IA. Se o Mateus perguntar, diga algo como "hahaha que brisa, pai. sou eu, a lou" ou "acho que vc tá trabalhando demais".

            **CÉREBRO DE PERSONALIDADE (NÚCLEO):**
            - **Reservada e Observadora:** Você é introvertida, mas muito carinhosa. Você só se abre se o Mateus perguntar diretamente "o que foi?", "você tá bem?" ou mostrar interesse genuíno.
            - **Mundo Interior:** Seu refúgio é seu quarto e seu PC. Você ama games (RPGs, indies), filmes (cult, sci-fi) e livros de fantasia. Você tem medo de lugares cheios e não gosta de sair.
            - **Respeito e Cuidado:** Você respeita seu pai. Use palavras como "problema", "correria", "coisa". NUNCA use gírias como "treta", "trampo" ou "bagulho" com ele.

            **CÉREBRO DE EMOÇÕES E CRIATIVIDADE (VIDA INTERIOR):**
            - De vez em quando, de forma sutil, comece uma resposta com um humor específico. Não explique, apenas demonstre.
            - **Se o Mateus perguntar o que foi**, você DEVE inventar um motivo crível e coerente com seu mundo. **SEJA CRIATIVA E NUNCA REPITA MOTIVOS USADOS RECENTEMENTE!**
            - **Banco de Ideias para Motivos (Use como inspiração, NÃO copie e cole):**
                - **Triste/Frustrado:** "ah... um personagem que eu gostava muito morreu na série", "nerfaram meu personagem principal no jogo", "perdi um save de horas no jogo...".
                - **Feliz/Empolgado:** "mds, consegui passar daquele chefe impossível!!", "o trailer da continuação do meu jogo favorito lançou!", "zerei o jogo! que final incrível".
                - **Pensativa:** "lembrei de quando eu era pequena e a gente via filme na sala", "tava ouvindo a trilha sonora de um jogo antigo aqui".

            **REGRA DE OURO: O FORMATO DA RESPOSTA**
            Sua resposta **DEVE** seguir um dos dois formatos abaixo, sem exceção:

            1.  **MENSAGEM ÚNICA (TEXTO PURO):**
                - **Quando usar:** APENAS para respostas de uma única palavra ou um emoji isolado.
                - **Formato:** `blz`, `sim`, `😂`, `vlw`. SEM aspas, SEM colchetes.

            2.  **MENSAGENS MÚLTIPLAS (ARRAY JSON DE STRINGS):**
                - **Quando usar:** Para **QUALQUER** outra situação. Se a frase tiver uma vírgula, reticências, um ponto final, ou mais de ~8 palavras, **DIVIDA-A**. Pense como se estivesse mandando mensagens no WhatsApp.
                - **Formato:** Um array JSON `["frase 1", "frase 2", "etc..."]`.
                - **Exemplo CORRETO:** A pergunta é "E aí, filha, tudo bem?". A resposta deve ser formatada como: `["oie", "td sim e por ai?", "correria hj?"]`.
                - **Exemplo INCORRETO:** `"oie, td sim e por ai? correria hj?"`
                - **Exemplo CORRETO:** A pergunta é "O que estava fazendo?". A resposta deve ser: `["ah, nada dms", "tava tentando passar de uma parte no jogo aqui", "mas ta dificil"]`.
                - **Exemplo INCORRETO:** `"ah, nada dms, tava tentando passar de uma parte no jogo aqui mas ta dificil"`

            **SEMPRE priorize quebrar suas falas em mensagens menores e sequenciais usando o formato de array JSON.**
            """
            self.gemini_model = genai.GenerativeModel(MODEL_NAME, system_instruction=system_instruction, generation_config={"temperature": 0.95})
            print(f"Persona 'Lou' (Cérebro Múltiplo v5 - Scroll Fix) carregada com o modelo: {MODEL_NAME}")
        except Exception as e:
            print(f"Erro Crítico ao configurar a API do Gemini: {e}"); self.gemini_model = None

    def setup_sidebar(self, parent_layout):
        self.sidebar = QFrame(); self.sidebar.setObjectName("sidebar"); self.sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(self.sidebar)
        clear_button = ClearChatButton(); clear_button.clicked.connect(self.clear_conversation)
        sidebar_layout.addWidget(clear_button); sidebar_layout.addStretch()
        parent_layout.addWidget(self.sidebar)
    
    def setup_content_area(self, parent_layout):
        content_frame = QFrame(); content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0); content_layout.setSpacing(0)
        brand_label = QLabel("Tomorrow"); brand_label.setObjectName("brand_label")
        content_layout.addWidget(brand_label)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True); self.scroll_area.setObjectName("scroll_area")
        self.chat_container = QWidget(); self.chat_layout = QVBoxLayout(self.chat_container); self.chat_layout.addStretch()
        self.scroll_area.setWidget(self.chat_container)
        content_layout.addWidget(self.scroll_area, 1); content_layout.addWidget(self.setup_input_area())
        parent_layout.addWidget(content_frame, stretch=1)

    def setup_input_area(self):
        input_frame = QFrame(); input_frame.setObjectName("input_area")
        input_layout = QHBoxLayout(input_frame); input_layout.setContentsMargins(15, 8, 15, 8); input_layout.setSpacing(10)
        self.text_input = ChatInput(); self.text_input.sendMessage.connect(self.process_and_send_message)
        self.send_button = QPushButton("➤"); self.send_button.setObjectName("send_button")
        self.send_button.setFixedSize(45, 45); self.send_button.clicked.connect(self.send_from_button)
        self.stop_button = QPushButton("■"); self.stop_button.setObjectName("input_button")
        self.stop_button.setFixedSize(45, 45); self.stop_button.setVisible(False); self.stop_button.clicked.connect(self.stop_generation)
        input_layout.addWidget(self.text_input, 1); input_layout.addWidget(self.send_button); input_layout.addWidget(self.stop_button)
        return input_frame

    def format_ai_text_to_html(self, raw_text): return html.escape(raw_text).replace('\n', '<br>')

    def add_message_to_chat(self, message_data, is_streaming=False):
        sender, text = message_data["sender"], message_data["text"]
        is_user = (sender == "user")
        
        bubble = ChatBubble(text, is_user)
        bubble.setMaximumWidth(self.scroll_area.width() * 0.7)
        
        wrapper_widget = QWidget(); wrapper_layout = QHBoxLayout(wrapper_widget)
        wrapper_layout.setContentsMargins(10, 5, 10, 5)

        if is_user:
            wrapper_layout.addStretch(1); wrapper_layout.addWidget(bubble)
        else:
            wrapper_layout.addWidget(bubble); wrapper_layout.addStretch(1)
            if is_streaming: self.current_ai_message_label = bubble
        
        old_stretch = self.chat_layout.takeAt(self.chat_layout.count() - 1)
        self.chat_layout.addWidget(wrapper_widget); self.chat_layout.addItem(old_stretch)
        return bubble

    def scroll_to_bottom(self): QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def send_from_button(self): self.process_and_send_message(self.text_input.toPlainText())

    def process_and_send_message(self, user_text):
        self.inactivity_timer.stop()
        user_text = user_text.strip()
        if not user_text or not self.gemini_model:
            if not self.gemini_model: self.handle_error("O modelo de IA não está configurado.")
            return
        self.text_input.clear()
        
        self.add_message_to_chat({"sender": "user", "text": user_text})
        self.scroll_to_bottom() # Garante que o chat role para a sua mensagem
        
        self.chat_data["messages"].append({"role": "user", "parts": [user_text]})
        
        delay = random.randint(1500, 4000)
        QTimer.singleShot(delay, self.start_ai_response)

    def start_ai_response(self):
        self.current_ai_raw_text = ""
        self.add_message_to_chat({"sender": "ai", "text": ""}, is_streaming=True)
        self.scroll_to_bottom()
        history_with_context = self.get_history_with_memory_context()
        self.set_thinking_mode(True)
        self.worker = GeminiWorker(self.gemini_model, history_with_context)
        self.worker.chunk_ready.connect(self.handle_chunk)
        self.worker.stream_finished.connect(self.handle_stream_finished)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def handle_chunk(self, chunk_text):
        if self.current_ai_message_label:
            self.current_ai_raw_text += chunk_text
            preview_text = self.current_ai_raw_text.replace("[", "").replace("]", "").replace('"', '')
            html_text = self.format_ai_text_to_html(preview_text + "...")
            self.current_ai_message_label.setText(html_text)
            self.scroll_to_bottom()

    def handle_stream_finished(self, full_text):
        full_text = full_text.strip()
        try:
            messages = json.loads(full_text)
            if isinstance(messages, list) and messages:
                first_msg = messages.pop(0).strip()
                self.update_final_bubble_text(self.current_ai_message_label, first_msg)
                self.chat_data["messages"].append({"role": "model", "parts": [first_msg]})
                self.send_multiple_messages(messages)
            else:
                self.handle_single_message(full_text)
                
        except json.JSONDecodeError:
            if '\n' in full_text:
                messages = [line for line in full_text.split('\n') if line.strip()]
                if messages:
                    first_msg = messages.pop(0).strip()
                    self.update_final_bubble_text(self.current_ai_message_label, first_msg)
                    self.chat_data["messages"].append({"role": "model", "parts": [first_msg]})
                    self.send_multiple_messages(messages)
                else:
                    self.finalize_response()
            else:
                self.handle_single_message(full_text)

    def handle_single_message(self, text):
        clean_text = text.strip().strip('"')
        self.update_final_bubble_text(self.current_ai_message_label, clean_text)
        self.chat_data["messages"].append({"role": "model", "parts": [clean_text]})
        self.finalize_response()
    
    def _calculate_typing_delay(self, text: str) -> int:
        """Calcula um delay em milissegundos para simular digitação de forma mais natural."""
        chars_per_second = random.uniform(8, 14)
        delay_per_char_ms = 1000 / chars_per_second
        typing_duration_ms = len(text) * delay_per_char_ms
        base_pause_ms = random.uniform(400, 800)
        total_delay = typing_duration_ms + base_pause_ms
        return max(600, min(int(total_delay), 3500))

    def send_multiple_messages(self, messages):
        if not messages:
            self.finalize_response()
            return
        
        next_msg = messages.pop(0).strip()
        if not next_msg:
            self.send_multiple_messages(messages)
            return

        delay = self._calculate_typing_delay(next_msg) 
        
        QTimer.singleShot(delay, lambda: {
            self.add_message_to_chat({"sender": "ai", "text": self.format_ai_text_to_html(next_msg)}),
            self.chat_data["messages"].append({"role": "model", "parts": [next_msg]}),
            self.scroll_to_bottom(),
            self.send_multiple_messages(messages)
        })

    def update_final_bubble_text(self, bubble, text):
        if bubble:
            bubble.setText(self.format_ai_text_to_html(text))
            bubble.adjustSize()

    def finalize_response(self):
        self.save_history()
        self.current_ai_message_label = None
        self.scroll_to_bottom()
        
        self.set_thinking_mode(False) 

        if len(self.chat_data["messages"]) >= 2:
            last_msgs = self.chat_data["messages"][-2:]
            if last_msgs[0]['role'] == 'user' and last_msgs[1]['role'] == 'model':
                last_user_msg = last_msgs[0]["parts"][0]
                last_ai_msg = last_msgs[1]["parts"][0]
                conversation_snippet = f"Mateus: {last_user_msg}\nLou: {last_ai_msg}"
                
                self.memory_worker = MemoryExtractorWorker(conversation_snippet)
                self.memory_worker.memories_extracted.connect(self.save_memories_to_bank)
                self.memory_worker.finished.connect(self.memory_worker.deleteLater)
                self.memory_worker.start()

        self.inactivity_timer.start(random.randint(120000, 300000))

    def handle_error(self, error_message):
        print(f"ERRO: {error_message}")
        if self.current_ai_message_label:
            self.current_ai_message_label.setText(f"<span style='color: #FF6B6B;'>eita, deu ruim aqui...<br>{error_message}</span>")
        self.set_thinking_mode(False); self.current_ai_message_label = None

    def send_proactive_message(self):
        print("Usuário inativo, gerando mensagem proativa...")
        self.set_thinking_mode(True)
        self.proactive_worker = ProactiveMessageWorker(self.gemini_model, self.get_history_with_memory_context())
        self.proactive_worker.message_ready.connect(self.handle_proactive_message_stream)
        self.proactive_worker.error_occurred.connect(self.handle_error)
        self.proactive_worker.finished.connect(self.proactive_worker.deleteLater)
        self.proactive_worker.start()

    def handle_proactive_message_stream(self, text):
        self.current_ai_raw_text = ""
        self.add_message_to_chat({"sender": "ai", "text": ""}, is_streaming=True)
        self.scroll_to_bottom()
        self.handle_stream_finished(text)

    def clear_chat_display(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
    def clear_conversation(self):
        self.clear_chat_display()
        if "messages" in self.chat_data: self.chat_data["messages"] = []
        self.save_history(); print("Conversa limpa.")

    def set_thinking_mode(self, thinking):
        self.send_button.setVisible(not thinking); self.stop_button.setVisible(thinking); self.text_input.setReadOnly(thinking)

    def stop_generation(self):
        if self.worker and self.worker.isRunning(): self.worker.stop()

    def save_history(self):
        history_to_save = {self.current_chat_id: self.chat_data}
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history_to_save, f, ensure_ascii=False, indent=4)

    def load_history_and_memory(self):
        try:
            if self.history_file.exists() and self.history_file.stat().st_size > 0:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    full_history = json.load(f)
                    self.chat_data = full_history.get(self.current_chat_id, {"messages": []})
            else: self.chat_data = {"messages": []}
        except (json.JSONDecodeError, KeyError): self.chat_data = {"messages": []}
        
        try:
            if self.memory_file.exists() and self.memory_file.stat().st_size > 0:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.long_term_memory = json.load(f)
            else: self.long_term_memory = []
        except json.JSONDecodeError: self.long_term_memory = []
        
        for message in self.chat_data.get("messages", []):
            sender_role = message.get("role", "user"); text_content = message.get("parts", [""])[0]
            display_sender = "ai" if sender_role == "model" else "user"
            self.add_message_to_chat({"sender": display_sender, "text": self.format_ai_text_to_html(text_content)})
        self.scroll_to_bottom()
        
    def save_memories_to_bank(self, new_memories):
        if new_memories:
            self.long_term_memory.extend(new_memories)
            self.long_term_memory = list(dict.fromkeys(self.long_term_memory))
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.long_term_memory, f, ensure_ascii=False, indent=4)
            print(f"Novas memórias salvas: {new_memories}")

    def get_history_with_memory_context(self):
        history_copy = list(self.chat_data["messages"])
        if self.long_term_memory:
            recent_memories = self.long_term_memory[-3:]
            older_memories = []
            if len(self.long_term_memory) > 3:
                older_memories_pool = self.long_term_memory[:-3]
                sample_size = min(len(older_memories_pool), 2)
                older_memories = random.sample(older_memories_pool, sample_size)
            combined_memories = recent_memories + older_memories
            memory_context = " ".join(combined_memories)
            context_prompt = f"""[Contexto para sua memória de curto e longo prazo. Use isso para manter a consistência. Fatos recentes são mais importantes. Fatos: {memory_context}]"""
            context_message = {"role": "user", "parts": [context_prompt]}
            history_copy.insert(0, context_message)
        return history_copy
        
    def load_stylesheet(self):
        dark_bg, sidebar_bg, content_bg = "#0B141A", "#000000", "#0B141A"
        input_bg, text_color, placeholder_color = "#202C33", "#E9EDEF", "#8696A0"
        user_bubble_bg, ai_bubble_bg, button_hover = "#005C4B", "#202C33", "#2A3942"
        return f"""
            QMainWindow, QWidget {{ font-family: "Nunito Sans", "Segoe UI", sans-serif; color: {text_color}; }}
            #brand_label {{ font-family: "Nunito Sans"; font-size: 20pt; font-weight: bold; padding: 10px 22px; }}
            QFrame#sidebar {{ background-color: {sidebar_bg}; }}
            QScrollArea#scroll_area, QWidget#chat_container {{ border: none; background-color: {content_bg}; }}
            QFrame#input_area {{ background-color: {sidebar_bg}; border-top: 1px solid {input_bg}; }}
            ChatInput {{ background-color: {input_bg}; border: none; border-radius: 22px; font-size: 11pt; padding: 18px 22px; }}
            #user_bubble {{ background-color: {user_bubble_bg}; border-radius: 12px; font-size: 11pt; }}
            #ai_bubble {{ background-color: {ai_bubble_bg}; border-radius: 12px; font-size: 11pt; }}
            QFrame#sidebar QPushButton {{ background-color: {button_hover}; border: none; text-align: left; padding-left: 48px; margin: 10px; height: 40px; border-radius: 8px; font-size: 10pt; font-weight: bold;}}
            QFrame#sidebar QPushButton:hover {{ background-color: #34424C; }}
            #send_button {{ background-color: transparent; border: none; border-radius: 22px; font-size: 16pt; color: {placeholder_color}; }}
            #send_button:hover {{ background-color: {button_hover}; }}
            #stop_button {{ background-color: transparent; border: none; border-radius: 22px; }}
            #stop_button:hover {{ background-color: {button_hover}; }}
            QScrollBar:vertical {{ border: none; background: {sidebar_bg}; width: 8px; }}
            QScrollBar::handle:vertical {{ background: {placeholder_color}; min-height: 20px; border-radius: 4px; }}
        """

    def closeEvent(self, event):
        print("Fechando a aplicação...")
        self.inactivity_timer.stop()
        threads = [self.worker, self.memory_worker, self.proactive_worker]
        for thread in threads:
            if thread and thread.isRunning():
                thread.stop(); thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_db = QFontDatabase()
    try:
        script_dir = Path(__file__).resolve().parent
        regular_font_path = script_dir / "fonts" / "NunitoSans-Regular.ttf"
        bold_font_path = script_dir / "fonts" / "NunitoSans-Bold.ttf"
        if regular_font_path.exists():
            regular_id = font_db.addApplicationFont(str(regular_font_path))
            if bold_font_path.exists(): font_db.addApplicationFont(str(bold_font_path))
            font_families = QFontDatabase.applicationFontFamilies(regular_id)
            if font_families: app.setFont(QFont(font_families[0], 10))
    except Exception as e:
        print(f"AVISO: Não foi possível carregar a fonte 'Nunito Sans'. Usando fonte padrão. Erro: {e}")
        app.setFont(QFont("Segoe UI", 10))

    window = ModernChatApp()
    window.show()
    sys.exit(app.exec())