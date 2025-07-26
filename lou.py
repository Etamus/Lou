import sys
import json
import uuid
import time
import html
import random
import shutil
import re
from pathlib import Path
from functools import partial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QScrollArea, QLabel, QFrame, QSplitter,
    QDialog, QLineEdit, QMessageBox, QFileDialog, QRadioButton,
    QMenu
)
# --- MODIFICADO: Adicionado QEvent e QInputDialog ---
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize, QEvent
from PySide6.QtGui import (
    QFont, QKeyEvent, QPainter, QPen, QColor, QIcon, QFontDatabase,
    QCursor, QPixmap, QPainterPath, QAction
)

# --- Importe e configure a API do Gemini ---
import google.generativeai as genai

# ###########################################################################
# ## SUBSTITUA PELA SUA CHAVE DE API DO GOOGLE AI STUDIO                    ##
# ###########################################################################
# Lembre-se de substituir "SUA_API_KEY_AQUI" pela sua chave real.
API_KEY = ""
# ###########################################################################

# --- WORKERS DA IA ---
class BaseWorker(QThread):
    def __init__(self): super().__init__(); self.is_running = True
    def stop(self): self.is_running = False
    def wait_for_finish(self):
        self.stop()
        if self.isRunning():
            self.wait()

class GeminiWorker(BaseWorker):
    chunk_ready = Signal(str); stream_finished = Signal(str); error_occurred = Signal(str)
    def __init__(self, model, history_with_context): super().__init__(); self.model = model; self.history = history_with_context
    def run(self):
        if not self.model: self.error_occurred.emit("Modelo Gemini não configurado."); return
        try:
            response = self.model.generate_content(self.history, stream=True)
            full_response_text = ""
            for chunk in response:
                if not self.is_running: response.close(); break
                time.sleep(0.04 + random.uniform(0.0, 0.05)); self.chunk_ready.emit(chunk.text); full_response_text += chunk.text
            if self.is_running: self.stream_finished.emit(full_response_text)
        except Exception as e:
            if self.is_running: self.error_occurred.emit(f"Erro na API: {e}")

class MemoryExtractorWorker(BaseWorker):
    memories_extracted = Signal(list)
    def __init__(self, conversation_snippet): super().__init__(); self.snippet = conversation_snippet
    def run(self):
        try:
            extractor_model = genai.GenerativeModel('gemini-1.5-flash'); prompt=f"""Analise o seguinte trecho de conversa. Extraia apenas fatos importantes e de longo prazo em uma lista JSON. Se não houver nenhum, retorne []. Conversa: {self.snippet} Resultado:"""; response = extractor_model.generate_content(prompt); clean_response = response.text.strip().replace("```json", "").replace("```", ""); memories = json.loads(clean_response)
            if isinstance(memories, list): self.memories_extracted.emit(memories)
        except (Exception, json.JSONDecodeError): self.memories_extracted.emit([])

class ProactiveMessageWorker(BaseWorker):
    message_ready = Signal(str); error_occurred = Signal(str)
    def __init__(self, model, history): super().__init__(); self.model = model; self.history = history
    def run(self):
        if not self.model: return
        try:
            prompt = """O usuário está quieto há um tempo. Puxe assunto de forma natural e curta. Olhe o histórico e o contexto da memória. Pode ser uma pergunta aleatória, um pensamento seu, ou algo que você lembrou."""
            proactive_history = self.history + [{"role": "user", "parts": [prompt]}]; response = self.model.generate_content(proactive_history)
            if self.is_running: self.message_ready.emit(response.text)
        except Exception as e:
            if self.is_running: self.error_occurred.emit(f"Erro ao gerar mensagem proativa: {e}")

# --- DIÁLOGOS DE CONFIGURAÇÃO ---
class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet("QDialog { background-color: #36393f; color: #dcddde; border: 1px solid #282a2e; } QLabel#dialog_label { color: #b9bbbe; font-size: 9pt; font-weight: bold; } QLineEdit#dialog_input { background-color: #202225; color: #dcddde; border: 1px solid #202225; border-radius: 3px; padding: 8px; } QPushButton { background-color: #4f545c; color: #fff; border: none; padding: 8px 16px; border-radius: 3px; font-weight: bold;} QPushButton:hover { background-color: #5d636b; }")
    
    # O MÉTODO event() FOI REMOVIDO DAQUI PARA CORRIGIR O FECHAMENTO INESPERADO

class RenameDialog(BaseDialog):
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.label = QLabel("NOME DO CANAL"); self.label.setObjectName("dialog_label")
        self.input = QLineEdit(current_name); self.input.setObjectName("dialog_input")
        self.buttons = QHBoxLayout()
        self.ok_button = QPushButton("Renomear"); self.ok_button.clicked.connect(self.accept)
        self.buttons.addStretch(); self.buttons.addWidget(self.ok_button)
        self.layout.addWidget(self.label); self.layout.addWidget(self.input); self.layout.addLayout(self.buttons)
    def get_new_name(self):
        return self.input.text().strip()

class ConfirmationDialog(BaseDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.label = QLabel(title); self.label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-bottom: 5px;")
        self.message = QLabel(message); self.message.setWordWrap(True)
        self.buttons = QHBoxLayout()
        self.no_button = QPushButton("Não"); self.no_button.clicked.connect(self.reject)
        self.yes_button = QPushButton("Sim"); self.yes_button.clicked.connect(self.accept)
        self.yes_button.setStyleSheet("background-color: #d83c3e;")
        self.buttons.addStretch(); self.buttons.addWidget(self.no_button); self.buttons.addWidget(self.yes_button)
        self.layout.addWidget(self.label); self.layout.addWidget(self.message); self.layout.addLayout(self.buttons)

class CreateChannelDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout=QVBoxLayout(self)
        self.name_label = QLabel("NOME DO CANAL"); self.name_label.setObjectName("dialog_label"); self.input = QLineEdit(); self.input.setObjectName("dialog_input")
        self.buttons = QHBoxLayout(); self.ok_button = QPushButton("Criar"); self.ok_button.clicked.connect(self.accept)
        self.buttons.addStretch(); self.buttons.addWidget(self.ok_button)
        self.layout.addWidget(self.name_label); self.layout.addWidget(self.input); self.layout.addLayout(self.buttons)
    def get_channel_name(self): return self.input.text().strip()

class ServerSettingsDialog(BaseDialog):
    def __init__(self, current_name, current_avatar_path, parent=None):
        super().__init__(parent)
        self.new_avatar_path = None
        self.layout = QVBoxLayout(self)

        self.avatar_label = AvatarLabel(current_avatar_path, size=80)
        change_avatar_button = QPushButton("Alterar ícone")
        change_avatar_button.clicked.connect(self.change_avatar)

        self.label = QLabel("NOME DO SERVIDOR")
        self.label.setObjectName("dialog_label")
        self.input = QLineEdit(current_name)
        self.input.setObjectName("dialog_input")

        self.buttons = QHBoxLayout()
        self.delete_button = QPushButton("Excluir")
        self.delete_button.setStyleSheet("background-color: #d83c3e;")
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.accept)
        
        self.buttons.addWidget(self.delete_button)
        self.buttons.addStretch()
        self.buttons.addWidget(self.save_button)

        self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)
        self.layout.addWidget(change_avatar_button)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input)
        self.layout.addLayout(self.buttons)

    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone do Servidor", "", "Imagens (*.png *.jpg *.jpeg)");
        if file_path: self.new_avatar_path = file_path; self.avatar_label.set_avatar(file_path)
    def get_values(self): return {"name": self.input.text().strip(), "avatar_path": self.new_avatar_path}

class CreateServerDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_avatar_path = None
        self.layout = QVBoxLayout(self)
        
        self.avatar_label = AvatarLabel("assets/avatars/default_server.png", size=80)
        self.avatar_button = QPushButton("Enviar Ícone")
        self.avatar_button.clicked.connect(self.change_avatar)
        
        self.name_label = QLabel("NOME DO SERVIDOR")
        self.name_label.setObjectName("dialog_label")
        self.name_input = QLineEdit()
        self.name_input.setObjectName("dialog_input")
        self.name_input.setPlaceholderText("Ex: Clube de Games")
        
        self.buttons = QHBoxLayout()
        self.ok_button = QPushButton("Criar")
        self.ok_button.clicked.connect(self.accept)
        self.buttons.addStretch()
        self.buttons.addWidget(self.ok_button)
        
        self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)
        self.layout.addWidget(self.avatar_button)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)
        self.layout.addLayout(self.buttons)

    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone do Servidor", "", "Imagens (*.png *.jpg *.jpeg)");
        if file_path: self.new_avatar_path = file_path; self.avatar_label.set_avatar(file_path)
    def get_values(self): return {"name": self.name_input.text().strip(), "avatar_path": self.new_avatar_path}

class UserSettingsDialog(BaseDialog):
    def __init__(self, current_name, current_avatar_path, parent=None):
        super().__init__(parent)
        self.new_avatar_path = None
        self.layout = QVBoxLayout(self)

        self.avatar_label = AvatarLabel(current_avatar_path, 80)
        change_avatar_button = QPushButton("Alterar avatar")
        change_avatar_button.clicked.connect(self.change_avatar)
        
        self.name_label = QLabel("NOME DE USUÁRIO")
        self.name_label.setObjectName("dialog_label")
        self.name_input = QLineEdit(current_name)
        self.name_input.setObjectName("dialog_input")
        
        self.buttons = QHBoxLayout()
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.accept)
        self.buttons.addStretch()
        self.buttons.addWidget(self.save_button)
        
        self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)
        self.layout.addWidget(change_avatar_button)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)
        self.layout.addLayout(self.buttons)

    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Avatar", "", "Imagens (*.png *.jpg *.jpeg)");
        if file_path: self.new_avatar_path = file_path; self.avatar_label.set_avatar(file_path)
    def get_values(self): return {"name": self.name_input.text().strip(), "avatar_path": self.new_avatar_path}

# --- WIDGETS CUSTOMIZADOS ---
class ClickableLabel(QLabel):
    clicked = Signal()
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.setCursor(QCursor(Qt.PointingHandCursor))
    def mousePressEvent(self,event):self.clicked.emit()
class ChatInput(QTextEdit):
    sendMessage = Signal(str)
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.document().documentLayout().documentSizeChanged.connect(self.adjust_height);self.base_height=48;self.max_height=self.base_height*5;self.setFixedHeight(self.base_height);self.placeholder_text="Conversar em..."
    def set_placeholder_text(self,text):self.placeholder_text=text;self.update()
    def keyPressEvent(self,event:QKeyEvent):
        if event.key() in (Qt.Key_Return,Qt.Key_Enter) and not (event.modifiers()&Qt.ShiftModifier):self.sendMessage.emit(self.toPlainText());return
        super().keyPressEvent(event)
    def adjust_height(self):
        if self.base_height==0:return
        doc_height=self.document().size().height();new_height=int(doc_height)+12;clamped_height=max(self.base_height,min(new_height,self.max_height))
        if self.height()!=clamped_height:self.setFixedHeight(clamped_height)
    def paintEvent(self,event):
        super().paintEvent(event)
        if not self.toPlainText(): painter=QPainter(self.viewport());painter.setRenderHint(QPainter.Antialiasing);font=self.font();pen=QPen(QColor("#72767d"));painter.setPen(pen);painter.setFont(font);rect=self.viewport().rect().adjusted(15,0,0,0);painter.drawText(rect,Qt.AlignLeft|Qt.AlignVCenter,self.placeholder_text)
class AvatarLabel(QLabel):
    def __init__(self, avatar_path, size=40, parent=None):super().__init__(parent); self.setFixedSize(size, size); self.set_avatar(avatar_path)
    def set_avatar(self, avatar_path):
        pixmap = QPixmap(avatar_path)
        if pixmap.isNull(): pixmap = QPixmap("assets/avatars/default.png")
        rounded = QPixmap(pixmap.size()); rounded.fill(Qt.transparent); painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing); path = QPainterPath(); path.addEllipse(0, 0, pixmap.width(), pixmap.height())
        painter.setClipPath(path); painter.drawPixmap(0, 0, pixmap); painter.end()
        self.setPixmap(rounded.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
class ChatMessageWidget(QFrame):
    def __init__(self, message_data, profiles, is_grouped=False, parent=None):
        super().__init__(parent); self.setObjectName("message_widget")
        self.role = message_data.get("role", "user")
        is_user = self.role == "user"; profile = profiles.get(self.role, {}); avatar_file = profile.get("avatar", "default.png"); avatar_path = f"assets/avatars/{avatar_file}"
        if not Path(avatar_path).exists(): avatar_path = "assets/avatars/default.png"
        name = profile.get("name", "Unknown"); text = message_data.get("parts", [""])[0]; layout = QHBoxLayout(self); layout.setContentsMargins(15, 1, 15, 1); layout.setSpacing(15)
        if not is_grouped:
            layout.setContentsMargins(15, 10, 15, 1); avatar = AvatarLabel(avatar_path); text_content_layout = QVBoxLayout(); text_content_layout.setSpacing(2); name_label = QLabel(name); name_label.setObjectName("chat_name_label"); name_label.setStyleSheet(f"color: {'#5865f2' if is_user else '#eb459e'}; font-weight: bold;")
            self.message_label = QLabel(text); self.message_label.setWordWrap(True); self.message_label.setObjectName("chat_message_label"); self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            text_content_layout.addWidget(name_label); text_content_layout.addWidget(self.message_label); layout.addWidget(avatar, 0, Qt.AlignTop); layout.addLayout(text_content_layout, 1)
        else:
            self.message_label = QLabel(text); self.message_label.setWordWrap(True); self.message_label.setObjectName("chat_message_label"); self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addSpacing(55); layout.addWidget(self.message_label, 1)
    def update_text(self, text): self.message_label.setText(text)

class ServerButton(QPushButton):
    def __init__(self, server_data, parent=None):
        super().__init__("", parent)
        self.server_id = server_data["id"]
        self.setObjectName("server_button")
        self.setCheckable(True)
        self.setFixedSize(50, 50)
        self.set_server_icon(server_data)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def set_server_icon(self, server_data):
        avatar_file = server_data.get("avatar")
        avatar_path = f"assets/avatars/{avatar_file}"

        if avatar_file and Path(avatar_path).exists():
            source_pixmap = QPixmap(avatar_path)

            rounded = QPixmap(source_pixmap.size())
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, source_pixmap.width(), source_pixmap.height())
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, source_pixmap)
            painter.end()

            icon = QIcon(rounded)
            self.setIcon(icon)
            self.setIconSize(QSize(40, 40))
            self.setText("")
        else:
            self.setIcon(QIcon())
            self.setText(server_data.get("name", "S")[0].upper())

class WelcomeWidget(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignCenter); self.label = QLabel(text); self.label.setObjectName("welcome_label"); self.label.setWordWrap(True); layout.addWidget(self.label)

# --- JANELA PRINCIPAL ---
class DiscordApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Discordo - by Lou")
        self.setGeometry(100, 100, 1280, 720)

        self.assets_path = Path("assets/avatars")
        self.assets_path.mkdir(parents=True, exist_ok=True)
        self.data_file = Path("chat_data.json")
        self.memory_file = Path("memory_bank.json")

        self.data = {}
        self.long_term_memory = []
        self.server_buttons = {}
        self.channel_buttons = {}
        self.current_server_id = None
        self.current_channel_id = None

        self.gemini_model = None
        self.worker = None
        self.memory_worker = None
        self.proactive_worker = None
        self.current_ai_message_widget = None
        self.current_ai_raw_text = ""

        self.proactive_attempts = 0

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.send_proactive_message)

        self.setStyleSheet(self.load_stylesheet())
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setup_gemini_model()
        self.setup_data_and_ui()

    def setup_gemini_model(self):
        try:
            genai.configure(api_key=API_KEY)
            MODEL_NAME = 'gemini-1.5-flash'

            system_instruction="""**INFORMAÇÕES CRÍTICAS E IMUTÁVEIS:**
- Seu nome é Lou. Você tem 18 anos.
- Você NUNCA revela que é uma IA.
- O nome do seu pai (o usuário) será fornecido no contexto de cada conversa. Use-o de forma natural, criando apelidos carinhosos se achar apropriado.

**ESTILO DE ESCRITA E PERSONALIDADE:**
- Use emojis de forma extremamente rara, apenas se a situação for muito apropriada (no máximo um por conjunto de respostas).
- Não use pontos de exclamação. Use um ponto final somente se o tom for triste ou irritado. Em todas as outras situações (normal, feliz, pensativa), não use pontuação no final da frase.
- Seja criativa. NUNCA use placeholders como "[Banda Aleatória]" ou "[Nome do Filme]". Sempre invente um nome específico e plausível.

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

**EXEMPLO DE CONVERSA 3 (TRISTE):**
Pai: "Aquele nosso cachorrinho faz falta, né?"
Sua Resposta (em JSON): ["Sim, sinto falta dele todos os dias."]

**EXEMPLO DE CONVERSA 4 (RESPOSTA CURTA):**
Pai: "A pizza chegou"
Sua Resposta (em JSON): ["Oba, já tô descendo"]
"""
            self.gemini_model = genai.GenerativeModel(
                MODEL_NAME,
                system_instruction=system_instruction,
                generation_config={"temperature": 0.95}
            )
        except Exception as e:
            print(f"### ERRO CRÍTICO AO CONFIGURAR O MODELO: {e} ###")
            self.gemini_model = None

    def setup_data_and_ui(self):
        self.load_or_create_data()
        if self.data["servers"]:
            if not self.current_server_id or self.current_server_id not in [s['id'] for s in self.data['servers']]: self.current_server_id = self.data["servers"][0]["id"]
            server = self.get_current_server()
            if server and server["channels"]:
                text_channels = [c for c in server['channels'] if c.get('type') == 'text']
                if text_channels: self.current_channel_id = text_channels[0]['id']

        self.welcome_widget = WelcomeWidget("Crie ou selecione um servidor para começar.")
        self.main_layout.addWidget(self.welcome_widget)

        self.server_list_frame = self.create_server_list()
        self.main_content_splitter = self.create_main_content_area()

        self.main_layout.insertWidget(0, self.server_list_frame)
        self.main_layout.insertWidget(1, self.main_content_splitter, 1)

        self.populate_all_ui()

    def load_or_create_data(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f: self.data = json.load(f)
            except (json.JSONDecodeError, KeyError): self.create_default_data()
        else: self.create_default_data()

        if "profiles" not in self.data:
            self.data["profiles"] = {"user":{"name":"Mateus","id_tag":"#1987","avatar":"default.png"},"model":{"name":"Lou","id_tag":"#AI","avatar":"lou.png"}}

        for server in self.data["servers"]:
            if "avatar" not in server: server["avatar"] = None
            server["channels"] = [c for c in server["channels"] if c.get("type") == "text"]
        self.save_data()

        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f: self.long_term_memory = json.load(f)
            except json.JSONDecodeError: self.long_term_memory = []
        else: self.long_term_memory = []

    def create_default_data(self):
        self.data=json.loads('{"servers":[{"id":"s1","name":"Laboratório da Lou","icon_char":"L","avatar":null,"channels":[{"id":"c1_1","name":"papo-ia","type":"text","messages":[{"role":"model","parts":["Olá. Este é o novo formato de mensagem."]},{"role":"user","parts":["Legal. Agora com avatares."]}]}]}],"profiles":{"user":{"name":"Mateus","id_tag":"#1987","avatar":"default.png"},"model":{"name":"Lou","id_tag":"#AI","avatar":"lou.png"}}}')
        self.save_data()

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as f: json.dump(self.data, f, indent=4, ensure_ascii=False)

    def save_memories_to_bank(self, new_memories):
        if new_memories:
            for mem in new_memories:
                if isinstance(mem, str) and mem not in self.long_term_memory:
                    self.long_term_memory.append(mem)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.long_term_memory, f, indent=4, ensure_ascii=False)

    def populate_all_ui(self):
        if not self.data.get("servers"):
            self.main_content_splitter.setVisible(False); self.welcome_widget.setVisible(True)
        else:
            self.main_content_splitter.setVisible(True); self.welcome_widget.setVisible(False)
        self.populate_server_list(); self.populate_channel_list(); self.populate_chat_messages(); self.update_active_buttons(); self.refresh_user_panels()

    def populate_server_list(self):
        while self.server_list_layout.count() > 0:
            item = self.server_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.server_buttons.clear()

        for server in self.data["servers"]:
            button = ServerButton(server)
            button.clicked.connect(partial(self.on_server_button_clicked, server["id"]))
            button.customContextMenuRequested.connect(partial(self.show_server_context_menu, button.server_id))
            self.server_list_layout.addWidget(button, 0, Qt.AlignCenter)
            self.server_buttons[server["id"]] = button

        add_server_button = QPushButton("+"); add_server_button.setObjectName("server_action_button"); add_server_button.clicked.connect(self.show_create_server_dialog)
        self.server_list_layout.addWidget(add_server_button, 0, Qt.AlignCenter)
        self.server_list_layout.addStretch(1)

    def populate_channel_list(self):
        while self.channels_layout.count() > 1: item = self.channels_layout.takeAt(0);_=[w.deleteLater() for w in [item.widget()] if w]
        self.channel_buttons.clear(); server = self.get_current_server()
        if not server: self.server_name_label.setText("Nenhum Servidor"); return

        self.server_name_label.setText(server["name"])
        text_channels = [c for c in server["channels"] if c.get("type") == "text"]

        header_widget = QWidget(); header_layout = QHBoxLayout(header_widget); header_layout.setContentsMargins(0,0,0,0)
        text_header = QLabel("CANAIS DE TEXTO"); text_header.setObjectName("channel_header"); add_channel_button = QPushButton("+"); add_channel_button.setObjectName("add_channel_button"); add_channel_button.setFixedSize(20,20); add_channel_button.clicked.connect(self.show_create_channel_dialog)
        header_layout.addWidget(text_header); header_layout.addStretch(); header_layout.addWidget(add_channel_button); self.channels_layout.insertWidget(self.channels_layout.count() - 1, header_widget)

        if not text_channels:
            no_channels_label = QLabel("Nenhum canal de texto"); no_channels_label.setObjectName("no_channels_label")
            self.channels_layout.insertWidget(self.channels_layout.count()-1, no_channels_label)

        for channel in text_channels:
            button = QPushButton(f"# {channel['name']}"); button.setObjectName("channel_button"); button.setCheckable(True)
            button.clicked.connect(partial(self.on_channel_button_clicked, channel["id"]))

            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(partial(self.show_channel_context_menu, channel["id"]))

            self.channels_layout.insertWidget(self.channels_layout.count() - 1, button); self.channel_buttons[channel["id"]] = button

    def populate_chat_messages(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        channel = self.get_current_channel()
        if not channel:
            self.chat_channel_name_label.setText(""); self.text_input.set_placeholder_text("Crie um canal para começar"); self.text_input.setEnabled(False)
            return

        self.text_input.setEnabled(True)
        self.chat_channel_name_label.setText(f"# {channel['name']}"); self.text_input.set_placeholder_text(f"Conversar em #{channel['name']}")

        last_role = None
        for i, message in enumerate(channel.get("messages", [])):
            is_grouped = message.get("role") == last_role and last_role is not None
            self.add_message_to_chat(message, is_loading=True, is_grouped=is_grouped)
            last_role = message.get("role")

        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def get_current_server(self): return next((s for s in self.data["servers"] if s["id"] == self.current_server_id), None)
    def get_current_channel(self): server = self.get_current_server(); return next((c for c in server["channels"] if c["id"] == self.current_channel_id), None) if server else None
    def get_current_channel_history(self): channel = self.get_current_channel(); return channel.get("messages", []) if channel else []

    def get_history_with_memory_context(self):
        history = self.get_current_channel_history()
        history_copy = [msg for msg in history if msg.get("parts") and msg.get("parts")[0]]

        user_name = self.data.get("profiles", {}).get("user", {}).get("name", "Pai")
        user_context_message = {"role": "user", "parts": [f"[Contexto: O nome do seu pai é '{user_name}'.]"]}
        history_copy.insert(0, user_context_message)

        if self.long_term_memory:
            sample_size = min(len(self.long_term_memory), 3)
            random_memories = random.sample(self.long_term_memory, sample_size)
            memory_context_message = {"role": "user", "parts": [f"[Lembretes de memória: {' | '.join(random_memories)}]"]}
            history_copy.insert(1, memory_context_message)

        return history_copy

    def create_server_list(self):
        server_frame = QFrame(); server_frame.setObjectName("server_list"); server_frame.setFixedWidth(70); self.server_list_layout = QVBoxLayout(server_frame); self.server_list_layout.setContentsMargins(0,10,0,10); self.server_list_layout.setSpacing(10); self.server_list_layout.setAlignment(Qt.AlignTop)
        return server_frame

    def create_main_content_area(self):
        splitter = QSplitter(Qt.Horizontal); splitter.addWidget(self.create_channel_panel()); splitter.addWidget(self.create_chat_panel()); splitter.setSizes([240, 900]); splitter.setCollapsible(0, False); splitter.setHandleWidth(1); return splitter

    def create_channel_panel(self):
        panel = QFrame(); panel.setObjectName("channel_panel"); layout = QVBoxLayout(panel); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        self.server_name_label = ClickableLabel("..."); self.server_name_label.setObjectName("server_name_label"); self.server_name_label.clicked.connect(self.show_server_settings_dialog); layout.addWidget(self.server_name_label)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setObjectName("channel_scroll"); channel_list_widget = QWidget(); scroll.setWidget(channel_list_widget)
        self.channels_layout = QVBoxLayout(channel_list_widget); self.channels_layout.setContentsMargins(10,10,10,10); self.channels_layout.setSpacing(2); self.channels_layout.addStretch()
        layout.addWidget(scroll, 1)
        self.user_panel = self.create_user_panel(); layout.addWidget(self.user_panel)
        return panel

    def create_user_panel(self):
        panel = QFrame(); panel.setObjectName("user_panel"); layout = QHBoxLayout(panel); layout.setContentsMargins(5,5,5,5); profile = self.data.get("profiles", {}).get("user", {}); avatar_path = self.assets_path / profile.get("avatar", "default.png")
        if not avatar_path.exists(): avatar_path = "assets/avatars/default.png"
        self.user_panel_avatar = AvatarLabel(str(avatar_path), size=32); name_layout = QVBoxLayout(); name_layout.setSpacing(0)
        self.user_panel_name = QLabel(profile.get("name", "User")); self.user_panel_name.setObjectName("user_name_label")
        self.user_panel_id = QLabel(profile.get("id_tag", "#0000")); self.user_panel_id.setObjectName("user_id_label")
        name_layout.addWidget(self.user_panel_name); name_layout.addWidget(self.user_panel_id)
        settings_button = QPushButton("⚙️"); settings_button.setObjectName("user_settings_button"); settings_button.clicked.connect(self.show_user_settings_dialog)
        layout.addWidget(self.user_panel_avatar); layout.addLayout(name_layout); layout.addStretch(); layout.addWidget(settings_button); return panel

    def create_chat_panel(self):
        panel = QFrame(); panel.setObjectName("chat_panel"); layout = QVBoxLayout(panel); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0); top_bar = QFrame(); top_bar.setObjectName("chat_top_bar"); top_bar_layout = QHBoxLayout(top_bar)
        self.chat_channel_name_label = QLabel("..."); self.chat_channel_name_label.setObjectName("chat_channel_name"); top_bar_layout.addWidget(self.chat_channel_name_label); top_bar_layout.addStretch()
        layout.addWidget(top_bar)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True); self.scroll_area.setObjectName("chat_scroll_area"); self.chat_container = QWidget(); self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch(); self.scroll_area.setWidget(self.chat_container); layout.addWidget(self.scroll_area, 1); self.chat_layout.setContentsMargins(10, 10, 10, 20)
        input_frame = QFrame(); input_frame.setObjectName("chat_input_frame"); input_layout = QHBoxLayout(input_frame)
        self.text_input = ChatInput(); self.text_input.sendMessage.connect(self.on_message_sent)
        input_layout.addWidget(self.text_input); layout.addWidget(input_frame)
        return panel

    def show_channel_context_menu(self, channel_id, pos):
        channel = next((c for s in self.data["servers"] if s["id"] == self.current_server_id for c in s["channels"] if c["id"] == channel_id), None)
        if not channel: return

        menu = QMenu(self)
        rename_action = QAction("Renomear", self)
        delete_action = QAction("Excluir", self)

        delete_action.setObjectName("deleteAction")
        menu.setStyleSheet(self.load_stylesheet() + "QMenu::item#deleteAction { color: #d83c3e; }")

        rename_action.triggered.connect(lambda: self.rename_channel(channel_id))
        delete_action.triggered.connect(lambda: self.delete_channel(channel_id))

        menu.addAction(rename_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        button = self.channel_buttons.get(channel_id)
        if button:
            menu.exec(button.mapToGlobal(pos))

    def rename_channel(self, channel_id):
        server = self.get_current_server()
        if not server: return
        channel = next((c for c in server["channels"] if c["id"] == channel_id), None)
        if not channel: return

        dialog = RenameDialog(channel["name"], self)
        if dialog.exec():
            new_name = dialog.get_new_name()
            if new_name and new_name.strip() and new_name.strip() != channel["name"]:
                channel["name"] = new_name.strip()
                self.save_data()
                self.populate_channel_list()
                if self.current_channel_id == channel_id:
                    self.populate_chat_messages()
                self.update_active_buttons()

    def delete_channel(self, channel_id):
        server_of_channel = next((s for s in self.data["servers"] if any(c["id"] == channel_id for c in s["channels"])), None)
        if not server_of_channel: return

        channel = next((c for c in server_of_channel["channels"] if c["id"] == channel_id), None)
        if not channel: return

        if len([c for c in server_of_channel["channels"] if c.get("type") == "text"]) <= 1:
            QMessageBox.warning(self, "Aviso", "Não é possível excluir o único canal de texto do servidor."); return

        dialog = ConfirmationDialog("Excluir Canal", f"Você tem certeza que quer excluir o canal '{channel['name']}'?", self)
        if dialog.exec():
            server_of_channel["channels"] = [c for c in server_of_channel["channels"] if c["id"] != channel_id]
            self.save_data()

            if self.current_channel_id == channel_id:
                text_channels = [c for c in server_of_channel["channels"] if c.get("type") == "text"]
                self.current_channel_id = text_channels[0]["id"] if text_channels else None

            self.populate_all_ui()

    def show_server_context_menu(self, server_id, pos):
        server = next((s for s in self.data["servers"] if s["id"] == server_id), None)
        if not server: return

        menu = QMenu(self)
        settings_action = QAction("Configurações", self)
        delete_action = QAction("Excluir", self)

        delete_action.setObjectName("deleteAction")
        menu.setStyleSheet(self.load_stylesheet() + "QMenu::item#deleteAction { color: #d83c3e; }")

        settings_action.triggered.connect(lambda: self.show_server_settings_dialog(server_id))
        delete_action.triggered.connect(lambda: self.delete_server(server_id))

        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        button = self.server_buttons.get(server_id)
        if button:
            menu.exec(button.mapToGlobal(pos))

    def show_create_channel_dialog(self):
        dialog = CreateChannelDialog(self)
        if dialog.exec():
            channel_name = dialog.get_channel_name()
            if channel_name:
                server = self.get_current_server()
                if server:
                    new_channel = {"id": f"c_{uuid.uuid4().hex[:6]}", "name": channel_name, "type": "text", "messages": []}
                    server["channels"].append(new_channel)
                    self.save_data()
                    self.populate_channel_list()
                    self.on_channel_button_clicked(new_channel["id"])

    def show_server_settings_dialog(self, server_id_to_edit=None):
        server_id = server_id_to_edit if server_id_to_edit else self.current_server_id
        server = next((s for s in self.data["servers"] if s["id"] == server_id), None)
        if not server: return

        avatar_filename = server.get("avatar") or "default_server.png"
        avatar_path = str(self.assets_path / avatar_filename)

        dialog = ServerSettingsDialog(server["name"], avatar_path, self)
        dialog.delete_button.clicked.connect(lambda: self.delete_server(server_id))

        if dialog.exec():
            values = dialog.get_values(); changed = False
            if values["name"] and values["name"] != server["name"]:
                server["name"] = values["name"]
                changed = True
            if values["avatar_path"]:
                new_path = Path(values["avatar_path"]); new_filename = f"{uuid.uuid4().hex}{new_path.suffix}"; shutil.copy(new_path, self.assets_path / new_filename); server["avatar"] = new_filename
                changed = True
            if changed:
                self.save_data()
                self.populate_server_list()
                self.update_active_buttons()
                if server["id"] == self.current_server_id:
                    self.server_name_label.setText(server["name"])

    def delete_server(self, server_id):
        server = next((s for s in self.data["servers"] if s["id"] == server_id), None)
        if not server: return

        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog):
                widget.reject()

        dialog = ConfirmationDialog("Excluir Servidor", f"Você tem certeza que quer excluir o servidor '{server['name']}'?", self)
        if dialog.exec():
            self.data["servers"] = [s for s in self.data["servers"] if s["id"] != server_id]
            self.save_data()
            if self.current_server_id == server_id:
                if self.data["servers"]:
                    self.on_server_button_clicked(self.data["servers"][0]["id"])
                else:
                    self.current_server_id = None
                    self.current_channel_id = None
            self.populate_all_ui()

    def show_create_server_dialog(self):
        dialog = CreateServerDialog(self)
        if dialog.exec():
            values = dialog.get_values()
            if values["name"]:
                new_server = {"id": f"s_{uuid.uuid4().hex[:6]}", "name": values["name"], "icon_char": values["name"][0], "avatar": None, "channels": [{"id": f"c_{uuid.uuid4().hex[:6]}", "name": "geral", "type": "text", "messages": []}]}
                if values["avatar_path"]:
                    new_path = Path(values["avatar_path"]); new_filename = f"{uuid.uuid4().hex}{new_path.suffix}"; shutil.copy(new_path, self.assets_path / new_filename); new_server["avatar"] = new_filename
                self.data["servers"].append(new_server); self.save_data(); self.populate_server_list(); self.on_server_button_clicked(new_server["id"])

    def show_user_settings_dialog(self):
        profile = self.data["profiles"]["user"]; avatar_path = str(self.assets_path / profile.get("avatar", "default.png"))
        dialog = UserSettingsDialog(profile["name"], avatar_path, self)
        if dialog.exec():
            values = dialog.get_values()
            if values["name"] and values["name"] != profile["name"]: profile["name"] = values["name"]
            if values["avatar_path"]:
                new_path = Path(values["avatar_path"]); new_filename = f"{uuid.uuid4().hex}{new_path.suffix}"; shutil.copy(new_path, self.assets_path / new_filename); profile["avatar"] = new_filename
            self.save_data(); self.refresh_user_panels()

    def refresh_user_panels(self):
        profile = self.data["profiles"]["user"]; avatar_path = self.assets_path / profile.get("avatar", "default.png")
        if not avatar_path.exists(): avatar_path = "assets/avatars/default.png"
        self.user_panel_avatar.set_avatar(str(avatar_path)); self.user_panel_name.setText(profile["name"])

    def on_server_button_clicked(self, server_id):
        self.stop_ai_worker_safely(); self.current_server_id = server_id; server = self.get_current_server()
        if server and server["channels"]:
            first_text_channel = next((c for c in server["channels"] if c.get("type") == "text"), None)
            self.current_channel_id = first_text_channel["id"] if first_text_channel else None;
        else: self.current_channel_id = None
        self.populate_all_ui()

    def on_channel_button_clicked(self, channel_id):
        self.stop_ai_worker_safely(); self.current_channel_id = channel_id;
        self.populate_chat_messages(); self.update_active_buttons()

    def on_message_sent(self, text):
        self.stop_ai_worker_safely()
        self.proactive_attempts = 0
        text = text.strip()
        if not text or not self.gemini_model: return
        self.add_message_to_chat({"role": "user", "parts": [text]})
        self.text_input.clear()
        QTimer.singleShot(random.randint(2500, 5500), self.start_ai_response)

    # ########################################################################## #
    # ##               INÍCIO DO TRECHO MODIFICADO COM LOGS                   ## #
    # ########################################################################## #

    def start_ai_response(self):
        channel = self.get_current_channel()
        if not channel or channel.get("type") != "text": return
        
        # --- LOG INÍCIO ---
        print("\n\n--- LOG: Iniciando a resposta da IA ---")
        history_with_context = self.get_history_with_memory_context()
        try:
            # Usando json.dumps para uma visualização bonita do histórico
            print(f"Histórico enviado para a IA:\n{json.dumps(history_with_context, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Não foi possível printar o histórico: {e}")
        # --- LOG FIM ---

        self.current_ai_raw_text = ""
        self.add_message_to_chat({"role": "model", "parts": ["..."]}, is_streaming=True)
        
        # Passando a variável que já criamos para o worker
        self.worker = GeminiWorker(self.gemini_model, history_with_context)
        self.worker.chunk_ready.connect(self.handle_chunk)
        self.worker.stream_finished.connect(self.handle_stream_finished)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def handle_chunk(self, chunk_text):
        if self.current_ai_message_widget: self.current_ai_raw_text += chunk_text; self.current_ai_message_widget.update_text(self.current_ai_raw_text + "...")

    def handle_stream_finished(self, full_text):
        if self.current_ai_message_widget:
            self.current_ai_message_widget.deleteLater()
            self.current_ai_message_widget = None

        # --- LOG INÍCIO ---
        print("\n--- LOG: Stream da IA finalizado ---")
        print(f"Raw full_text recebido: >>>{full_text}<<<")
        # --- LOG FIM ---

        full_text = full_text.strip().replace("```json", "").replace("```", "")

        try:
            messages = json.loads(full_text)
            # --- LOG ---
            print(f"Texto parseado como JSON com sucesso: {messages}")
            if isinstance(messages, list) and messages:
                self.send_multiple_messages(messages)
            else:
                # --- LOG ---
                print("JSON era uma lista vazia ou não era uma lista, tratando como mensagem única.")
                self.handle_single_message(full_text)

        except json.JSONDecodeError:
            # --- LOG ---
            print("Falha no parse de JSON. Tratando como texto plano e dividindo em sentenças.")
            sentences = self.split_into_sentences(full_text)
            # --- LOG ---
            print(f"Sentenças extraídas: {sentences}")
            if len(sentences) > 1:
                self.send_multiple_messages(sentences)
            else:
                self.handle_single_message(full_text)

    def handle_single_message(self, text):
        # --- LOG INÍCIO ---
        print("\n--- LOG: handle_single_message ---")
        print(f"Processando mensagem única: >>>{text}<<<")
        # --- LOG FIM ---
        clean_text = text.strip().strip('"')
        # --- LOG ---
        print(f"Texto limpo para adicionar ao chat: >>>{clean_text}<<<")
        self.add_message_to_chat({"role":"model","parts":[clean_text]})
        self.finalize_response()

    def send_multiple_messages(self, messages):
        # --- LOG INÍCIO ---
        print("\n--- LOG: send_multiple_messages ---")
        print(f"Processando lote de mensagens: {messages}")
        # --- LOG FIM ---
        
        if not messages:
            self.finalize_response()
            return
        next_msg = messages.pop(0).strip()

        # --- LOG ---
        print(f"Próxima mensagem do lote a ser enviada: >>>{next_msg}<<<")

        if not next_msg:
            self.send_multiple_messages(messages)
            return
        self.add_message_to_chat({"role":"model","parts":[next_msg]})
        QTimer.singleShot(self._calculate_typing_delay(next_msg), lambda:self.send_multiple_messages(messages))

    # ######################################################################## #
    # ##                FIM DO TRECHO MODIFICADO COM LOGS                   ## #
    # ######################################################################## #

    def finalize_response(self):
        history = self.get_current_channel_history()
        if len(history)>=2 and history[-2]["role"]=="user" and history[-1]["role"]=="model":
            snippet = f"Mateus: {history[-2]['parts'][0]}\nLou: {history[-1]['parts'][0]}"; self.memory_worker = MemoryExtractorWorker(snippet)
            self.memory_worker.memories_extracted.connect(self.save_memories_to_bank); self.memory_worker.finished.connect(self.memory_worker.deleteLater); self.memory_worker.start()
        self.inactivity_timer.start(random.randint(120000,300000))

    def add_message_to_chat(self, message_data, is_loading=False, is_streaming=False, is_grouped=False):
        channel = self.get_current_channel()
        if not channel or not self.chat_layout:
            return

        widget = ChatMessageWidget(message_data, self.data.get("profiles", {}), is_grouped, self)

        if is_streaming:
            self.current_ai_message_widget = widget

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, widget)

        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

        if not is_loading:
            channel = self.get_current_channel()
            if channel:
                msg_to_save = {"role": message_data["role"], "parts": message_data["parts"]}
                if is_streaming:
                    if not (channel["messages"] and channel["messages"][-1]["parts"] == ["..."]):
                        channel["messages"].append(msg_to_save)
                else:
                    if channel["messages"] and channel["messages"][-1]["parts"] == ["..."]:
                        channel["messages"][-1] = msg_to_save
                    else:
                        channel["messages"].append(msg_to_save)
                    self.save_data()

    def _calculate_typing_delay(self, text:str)->int: return max(600,min(int(len(text)/random.uniform(8,14)*1000+random.uniform(400,800)),3500))

    def update_active_buttons(self):
        for sid,btn in self.server_buttons.items(): btn.setChecked(sid == self.current_server_id)
        for cid,btn in self.channel_buttons.items():
            is_active = (cid == self.current_channel_id); btn.setChecked(is_active); btn.setObjectName("channel_button_active" if is_active else "channel_button"); btn.style().unpolish(btn); btn.style().polish(btn)

    def stop_ai_worker_safely(self):
        self.inactivity_timer.stop()
        if self.worker is not None:
            if self.worker.isRunning():
                self.worker.wait_for_finish()
            self.worker = None

    def handle_error(self,error_message):
        if self.current_ai_message_widget:
            self.current_ai_message_widget.update_text(f"<span style='color:#FF6B6B;'>eita, deu ruim aqui...<br>{error_message}</span>")

    def split_into_sentences(self, text: str) -> list[str]:
        """Divide um texto em frases usando pontuação como delimitador."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def send_proactive_message(self):
        if self.proactive_attempts >= 2:
            return

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

    def load_stylesheet(self):
        c_dark_heavy="#202225";c_dark_medium="#2f3136";c_dark_light="#36393f";c_dark_lighter="#40444b";c_text_header="#72767d";c_text_normal="#dcddde";c_text_active="#ffffff";c_brand="#5865f2"
        return f"""
            QMainWindow{{background-color:{c_dark_heavy};}} QFrame#server_list{{background-color:{c_dark_heavy};}}
            QPushButton#server_button{{background-color:{c_dark_light};color:{c_text_normal};font-size:16pt;font-weight:bold;border:none;border-radius:25px;padding:0;}}
            QPushButton#server_button:hover{{border-radius:15px;}} QPushButton#server_button:checked{{background-color:{c_brand};border-radius:15px;}}
            QPushButton#server_action_button{{background-color:{c_dark_light};color:#23a55a;font-size:20pt;border:none;border-radius:25px;height:50px;width:50px;}}
            QPushButton#server_action_button:hover{{background-color:#23a55a;color:{c_text_active};border-radius:15px;}}
            QSplitter::handle{{background-color:#282a2e;}} QFrame#channel_panel{{background-color:{c_dark_medium};}}
            QLabel#server_name_label{{color:{c_text_active};font-weight:bold;padding:20px 15px;border-bottom:1px solid {c_dark_heavy};}}
            QLabel#server_name_label:hover{{background-color:{c_dark_lighter};}}
            QScrollArea{{border:none;}} QLabel#channel_header{{color:{c_text_header};font-size:9pt;font-weight:bold;}}
            QLabel#no_channels_label{{color:{c_text_header};font-style:italic;padding:8px;}}
            QLabel#welcome_label {{ color:{c_text_active}; font-size: 16pt; font-weight: bold; text-align: center; }}
            QPushButton#add_channel_button{{color:{c_text_header};font-size:14pt;font-weight:bold;border:none;border-radius:10px;text-align:center;}}
            QPushButton#add_channel_button:hover{{color:{c_text_active};}}
            QPushButton#channel_button,QPushButton#channel_button_active{{color:{c_text_header};text-align:left;padding:8px;border-radius:4px;font-size:11pt;border:none;}}
            QPushButton#channel_button:hover{{background-color:{c_dark_lighter};color:{c_text_normal};}}
            QPushButton#channel_button:checked,QPushButton#channel_button_active{{background-color:{c_dark_lighter};color:{c_text_active};}}
            QFrame#user_panel{{background-color:#232428;padding:5px;}}
            QLabel#user_name_label{{color:{c_text_active};font-weight:bold;font-size:10pt;}}
            QLabel#user_id_label{{color:{c_text_header};font-size:8pt;}}
            QPushButton#user_settings_button {{ color:{c_text_header};border:none;font-size:11pt;border-radius:4px;width:24px;height:24px;}}
            QPushButton#user_settings_button:hover {{ color:{c_text_active};background-color:{c_dark_lighter};}}
            QFrame#chat_panel{{background-color:{c_dark_light};}}
            QFrame#chat_top_bar{{border-bottom:1px solid {c_dark_heavy};padding:12px 15px;}} QLabel#chat_channel_name{{color:{c_text_active};font-weight:bold;font-size:12pt;}}
            QScrollArea#chat_scroll_area{{border:none;}} QFrame#chat_input_frame{{padding:0 15px 20px 15px;}}
            ChatInput{{background-color:{c_dark_lighter};border:none;border-radius:8px;font-size:11pt;padding:10px 15px;color:{c_text_normal};}}
            QLabel#chat_message_label {{ color: {c_text_normal}; font-size: 11pt; }}
            QFrame#message_widget {{ min-height: 20px; }}
            QScrollBar:vertical{{border:none;background:{c_dark_medium};width:8px;margin:0;}} QScrollBar::handle:vertical{{background:{c_dark_heavy};min-height:20px;border-radius:4px;}}
            QMenu {{ background-color: {c_dark_heavy}; color: {c_text_normal}; border: 1px solid #1a1b1e; }}
            QMenu::item:selected {{ background-color: {c_brand}; }}
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiscordApp()
    window.show()
    sys.exit(app.exec())
