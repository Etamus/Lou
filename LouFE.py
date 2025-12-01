# LouFE.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QScrollArea, QLabel,
    QFrame, QSplitter, QDialog, QLineEdit, QFileDialog, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import (
    QFont, QKeyEvent, QPainter, QPen, QColor, QIcon, QCursor, QPixmap, QPainterPath, QAction, QMovie
)
from datetime import datetime

# --- DIÁLOGOS DE CONFIGURAÇÃO ---
# Em LouFE.py, substitua esta classe

class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet("""
            QDialog { background-color: #36393f; color: #dcddde; border: 1px solid #282a2e; } 
            QLabel#dialog_label { color: #b9bbbe; font-size: 9pt; font-weight: bold; } 
            QLineEdit#dialog_input { background-color: #202225; color: #dcddde; border: 1px solid #202225; border-radius: 3px; padding: 8px; } 
            
            /* Estilos de Botão Padronizados */
            QPushButton { border: none; padding: 8px 16px; border-radius: 3px; font-weight: bold; }
            
            QPushButton#secondaryButton { background-color: #4f545c; color: #ffffff; }
            QPushButton#secondaryButton:hover { background-color: #5d636b; }
            
            QPushButton#deleteButton { background-color: #d83c3e; color: #ffffff; }
            QPushButton#deleteButton:hover { background-color: #a32d2f; }
            
            QPushButton#primaryButton { background-color: #4f5acb; color: #ffffff; }
            QPushButton#primaryButton:hover { background-color: #5f6ad2; } /* <-- EFEITO HOVER ADICIONADO */

            /* Estilo corrigido para o botão 'X' */
            QPushButton#dialogCloseButton {
                background-color: transparent; color: #b9bbbe;
                font-size: 18pt; /* <-- Tamanho da fonte aumentado */
                font-weight: bold;
                padding: 2px 6px; /* <-- Padding ajustado para dar mais altura */
                min-width: 20px;
            }
            QPushButton#dialogCloseButton:hover { color: #ffffff; }
        """)
    
    def _add_close_button_to_layout(self, target_layout):
        close_button = QPushButton("×"); close_button.setObjectName("dialogCloseButton")
        close_button.setCursor(QCursor(Qt.PointingHandCursor)); close_button.clicked.connect(self.reject)
        top_bar_layout = QHBoxLayout(); top_bar_layout.addStretch(); top_bar_layout.addWidget(close_button)
        target_layout.insertLayout(0, top_bar_layout)

# Em LouFE.py, substitua esta classe

class RenameDialog(BaseDialog):
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.label = QLabel("NOME DO CANAL"); self.label.setObjectName("dialog_label")
        self.input = QLineEdit(current_name); self.input.setObjectName("dialog_input")
        self.buttons = QHBoxLayout()
        cancel_button = QPushButton("Cancelar"); cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("Salvar"); self.ok_button.setObjectName("primaryButton")
        self.ok_button.clicked.connect(self.accept)
        self.buttons.addStretch(); self.buttons.addWidget(cancel_button); self.buttons.addWidget(self.ok_button)
        self.layout.addWidget(self.label); self.layout.addWidget(self.input); self.layout.addLayout(self.buttons)
    def get_new_name(self): return self.input.text().strip()

# Em LouFE.py, substitua a classe ConfirmationDialog

# Em LouFE.py, substitua esta classe

class ConfirmationDialog(BaseDialog):
    def __init__(self, title, message, parent=None, add_close_button=True):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        if add_close_button:
            self._add_close_button_to_layout(self.layout)
            
        self.label = QLabel(title); self.label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-bottom: 5px;")
        self.message = QLabel(message); self.message.setWordWrap(True)
        
        self.buttons = QHBoxLayout()
        # --- CORREÇÃO APLICADA AQUI ---
        self.no_button = QPushButton("Não"); self.no_button.setObjectName("secondaryButton")
        self.no_button.clicked.connect(self.reject)
        
        self.yes_button = QPushButton("Sim"); self.yes_button.setObjectName("deleteButton")
        self.yes_button.clicked.connect(self.accept)
        
        self.buttons.addStretch()
        self.buttons.addWidget(self.no_button)
        self.buttons.addWidget(self.yes_button)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.message)
        self.layout.addLayout(self.buttons)

# Em LouFE.py, substitua esta classe

class CreateChannelDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout=QVBoxLayout(self)
        self.name_label = QLabel("NOME DO CANAL"); self.name_label.setObjectName("dialog_label")
        self.input = QLineEdit(); self.input.setObjectName("dialog_input")
        self.buttons = QHBoxLayout()
        cancel_button = QPushButton("Cancelar"); cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("Criar"); self.ok_button.setObjectName("primaryButton")
        self.ok_button.clicked.connect(self.accept)
        self.buttons.addStretch(); self.buttons.addWidget(cancel_button); self.buttons.addWidget(self.ok_button)
        self.layout.addWidget(self.name_label); self.layout.addWidget(self.input); self.layout.addLayout(self.buttons)
    def get_channel_name(self): return self.input.text().strip()

# Em LouFE.py, substitua esta classe

class ServerSettingsDialog(BaseDialog):
    def __init__(self, current_name, current_avatar_path, parent=None):
        super().__init__(parent)
        self.new_avatar_path = None
        self.layout = QVBoxLayout(self)
        self._add_close_button_to_layout(self.layout)
        self.avatar_label = AvatarLabel(current_avatar_path, size=80, clickable=True)
        self.avatar_label.setToolTip("Clique para alterar o ícone")
        self.avatar_label.clicked.connect(self.change_avatar)
        self.label = QLabel("NOME DO SERVIDOR"); self.label.setObjectName("dialog_label")
        self.input = QLineEdit(current_name); self.input.setObjectName("dialog_input")
        self.buttons = QHBoxLayout()
        self.delete_button = QPushButton("Excluir"); self.delete_button.setObjectName("deleteButton")
        self.save_button = QPushButton("Salvar"); self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.accept)
        self.buttons.addStretch(); self.buttons.addWidget(self.delete_button); self.buttons.addWidget(self.save_button)
        self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.label); self.layout.addWidget(self.input)
        self.layout.addLayout(self.buttons)
    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone do Servidor", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path: self.new_avatar_path = file_path; self.avatar_label.set_avatar(file_path)
    def get_values(self): return {"name": self.input.text().strip(), "avatar_path": self.new_avatar_path}

# Em LouFE.py, substitua esta classe

class CreateServerDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_avatar_path = None
        self.layout = QVBoxLayout(self)
        self.avatar_label = AvatarLabel("assets/avatars/default_server.png", size=80, clickable=True)
        self.avatar_label.setToolTip("Clique para alterar o ícone")
        self.avatar_label.clicked.connect(self.change_avatar)
        self.name_label = QLabel("NOME DO SERVIDOR"); self.name_label.setObjectName("dialog_label")
        self.name_input = QLineEdit(); self.name_input.setObjectName("dialog_input"); self.name_input.setPlaceholderText("Ex: Grupo da Lou")
        self.buttons = QHBoxLayout()
        cancel_button = QPushButton("Cancelar"); cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("Criar"); self.ok_button.setObjectName("primaryButton")
        self.ok_button.clicked.connect(self.accept)
        self.buttons.addStretch(); self.buttons.addWidget(cancel_button); self.buttons.addWidget(self.ok_button)
        self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.name_label); self.layout.addWidget(self.name_input)
        self.layout.addLayout(self.buttons)
    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone do Servidor", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path: self.new_avatar_path = file_path; self.avatar_label.set_avatar(file_path)
    def get_values(self): return {"name": self.name_input.text().strip(), "avatar_path": self.new_avatar_path}

# Em LouFE.py, substitua esta classe

class UserSettingsDialog(BaseDialog):
    def __init__(self, profiles_data, assets_path, parent=None):
        super().__init__(parent)
        self.profiles_data = profiles_data
        self.assets_path = assets_path
        self.current_profile_key = "user" # Começa editando o perfil do usuário
        self.new_avatar_path = None

        self.layout = QVBoxLayout(self)
        
        # --- Botão para alternar entre perfis (sem o 'X') ---
        self.switch_button = QPushButton("↻")
        self.switch_button.setObjectName("dialogCloseButton")
        self.switch_button.setToolTip("Alternar perfil")
        self.switch_button.clicked.connect(self._toggle_profile_view)
        
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.switch_button)
        self.layout.addLayout(top_bar_layout) # Adiciona a barra do topo

        # --- Widgets da UI (serão atualizados dinamicamente) ---
        self.avatar_label = AvatarLabel("", 80, clickable=True)
        self.avatar_label.clicked.connect(self.change_avatar)
        
        self.title_label = QLabel(""); self.title_label.setObjectName("dialog_label")
        self.name_input = QLineEdit(); self.name_input.setObjectName("dialog_input")
        
        # --- Botões de Ação ---
        self.buttons = QHBoxLayout()
        cancel_button = QPushButton("Cancelar"); cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton("Salvar"); self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.accept)
        self.buttons.addStretch(); self.buttons.addWidget(cancel_button); self.buttons.addWidget(self.save_button)
        
        self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.name_input)
        self.layout.addLayout(self.buttons)

        self._update_ui_for_profile() # Popula a UI com o perfil inicial (usuário)

    def _toggle_profile_view(self):
        """Alterna a visualização entre o perfil do usuário e o da Lou."""
        self.new_avatar_path = None # Reseta o caminho do avatar ao trocar
        if self.current_profile_key == "user":
            self.current_profile_key = "model"
        else:
            self.current_profile_key = "user"
        
        self._update_ui_for_profile()

    def _update_ui_for_profile(self):
        """Atualiza os widgets da UI com os dados do perfil selecionado."""
        profile_data = self.profiles_data[self.current_profile_key]
        
        # Define o título (TEXTO ALTERADO)
        if self.current_profile_key == "user":
            self.title_label.setText("NOME DE USUÁRIO")
            self.switch_button.setToolTip("Alternar para o perfil da Lou")
        else:
            self.title_label.setText("NOME DA IA")
            self.switch_button.setToolTip("Alternar para o seu perfil")
        
        # Define o nome no campo de input
        self.name_input.setText(profile_data.get("name", ""))
        
        # Define o avatar
        avatar_path = self.assets_path / profile_data.get("avatar", "default.png")
        if not avatar_path.exists():
            avatar_path = self.assets_path / "default.png"
        self.avatar_label.set_avatar(str(avatar_path))
        self.avatar_label.setToolTip(f"Clique para alterar o avatar de {profile_data.get('name', '')}")

    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Avatar", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.new_avatar_path = file_path
            self.avatar_label.set_avatar(file_path)

    def get_values(self):
        """Retorna qual perfil foi editado e os novos valores."""
        return {
            "profile_key": self.current_profile_key,
            "name": self.name_input.text().strip(),
            "avatar_path": self.new_avatar_path
        }

# --- O restante do arquivo (ChatMessageWidget, UIMixin, etc.) permanece o mesmo ---
# (O código foi omitido por brevidade, mas você deve mantê-lo no seu arquivo)
class ClickableLabel(QLabel):
    clicked = Signal(); 
    def __init__(self,*args,**kwargs): super().__init__(*args,**kwargs); self.setCursor(QCursor(Qt.PointingHandCursor))
    def mousePressEvent(self,event): self.clicked.emit()
class ChatInput(QTextEdit):
    sendMessage = Signal(str); 
    def __init__(self,*args,**kwargs): super().__init__(*args,**kwargs); self.document().documentLayout().documentSizeChanged.connect(self.adjust_height); self.base_height=48; self.max_height=self.base_height*5; self.setFixedHeight(self.base_height); self.placeholder_text="Conversar em..."
    def set_placeholder_text(self,text): self.placeholder_text=text; self.update()
    def keyPressEvent(self,event:QKeyEvent):
        if event.key() in (Qt.Key_Return,Qt.Key_Enter) and not (event.modifiers()&Qt.ShiftModifier): self.sendMessage.emit(self.toPlainText()); return
        super().keyPressEvent(event)
    def adjust_height(self):
        if self.base_height==0: return
        doc_height=self.document().size().height(); new_height=int(doc_height)+12; clamped_height=max(self.base_height,min(new_height,self.max_height))
        if self.height()!=clamped_height: self.setFixedHeight(clamped_height)
    def paintEvent(self,event):
        super().paintEvent(event)
        if not self.toPlainText(): painter=QPainter(self.viewport()); painter.setRenderHint(QPainter.Antialiasing); font=self.font(); pen=QPen(QColor("#72767d")); painter.setPen(pen); painter.setFont(font); rect=self.viewport().rect().adjusted(15,0,0,0); painter.drawText(rect,Qt.AlignLeft|Qt.AlignVCenter,self.placeholder_text)
class AvatarLabel(QLabel): # <-- Voltando a herdar de QLabel
    clicked = Signal()

    def __init__(self, avatar_path, size=40, clickable=False, parent=None):
        super().__init__(parent)
        self._clickable = clickable # Armazena o estado
        if self._clickable:
            self.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.setFixedSize(size, size)
        self.set_avatar(avatar_path)
        
    def mousePressEvent(self, event):
        if self._clickable: # Só emite o sinal se for clicável
            self.clicked.emit()

    def set_avatar(self, avatar_path):
        pixmap = QPixmap(avatar_path)
        if pixmap.isNull(): pixmap = QPixmap("assets/avatars/default.png")
        rounded = QPixmap(pixmap.size()); rounded.fill(Qt.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing); path = QPainterPath()
        path.addEllipse(0, 0, pixmap.width(), pixmap.height())
        painter.setClipPath(path); painter.drawPixmap(0, 0, pixmap); painter.end()
        self.setPixmap(rounded.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
class ReplyIndicatorWidget(QFrame):
    reply_cancelled = Signal()
    def __init__(self, profiles, parent=None):
        super().__init__(parent)
        self.setObjectName("reply_indicator")
        self.profiles = profiles
        self.setFixedHeight(40)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(15, 5, 15, 5)
        self.main_layout.setSpacing(8)
        self.avatar_label = AvatarLabel("assets/avatars/default.png", size=20)
        self.name_label = QLabel("Nome")
        self.name_label.setObjectName("replyNameLabel")
        self.message_label = QLabel("Mensagem...")
        self.message_label.setObjectName("replyMessageLabel")
        self.cancel_button = QPushButton("×")
        self.cancel_button.setObjectName("replyCancelButton")
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.clicked.connect(self.reply_cancelled.emit)
        self.main_layout.addWidget(self.avatar_label)
        self.main_layout.addWidget(self.name_label)
        self.main_layout.addWidget(self.message_label, 1)
        self.main_layout.addWidget(self.cancel_button)
        self.setStyleSheet("""
            QFrame#reply_indicator { background-color: #2f3136; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QLabel#replyNameLabel { color: #eb459e; font-weight: bold; }
            QLabel#replyMessageLabel { color: #b9bbbe; }
            QPushButton#replyCancelButton { color: #b9bbbe; border: none; font-size: 18pt; padding-bottom: 5px; }
            QPushButton#replyCancelButton:hover { color: #ffffff; }
        """)
        self.hide()
    def set_reply_message(self, message_data):
        role = message_data.get("role", "model")
        profile = self.profiles.get(role, {})
        avatar_file = profile.get("avatar", "default.png")
        avatar_path = f"assets/avatars/{avatar_file}"
        self.avatar_label.set_avatar(avatar_path)
        self.name_label.setText(profile.get("name", "Desconhecido"))
        text = message_data.get("parts", [""])[0]
        if len(text) > 60: text = text[:60] + "..."
        self.message_label.setText(text)
        self.show()
# Em LouFE.py, substitua a classe ChatMessageWidget

class ChatMessageWidget(QFrame):
    reply_clicked = Signal(dict)
    def __init__(self, message_data, profiles, is_grouped=False, parent=None, show_reply_button=True):
        from pathlib import Path
        super().__init__(parent)
        self.setObjectName("message_widget")
        self.setMouseTracking(True)
        self.message_data = message_data
        self.profiles = profiles
        self.role = message_data.get("role", "user")
        is_user = self.role == "user"
        profile = self.profiles.get(self.role, {})
        name = profile.get("name", "Unknown")
        text_content = message_data.get("parts", [""])[0]
        timestamp_str = message_data.get("timestamp")
        is_a_reply = "is_reply_to" in self.message_data and self.role == "user"
        if is_a_reply:
            text_content = text_content.split("\n")[-1]
        is_gif = text_content.startswith("GIF:")
        main_vertical_layout = QVBoxLayout(self)
        if is_a_reply: top_margin = 15
        elif is_grouped: top_margin = 1
        else: top_margin = 10
        main_vertical_layout.setContentsMargins(0, top_margin, 0, 0)
        main_vertical_layout.setSpacing(0)
        if is_a_reply:
            # ... (código do banner de resposta)
            reply_data = self.message_data["is_reply_to"]
            reply_profile = self.profiles.get(reply_data.get("role", "model"), {})
            reply_banner_widget = QWidget()
            reply_banner_layout = QHBoxLayout(reply_banner_widget)
            reply_banner_layout.setContentsMargins(55, 0, 15, 4)
            reply_banner_layout.setSpacing(6)
            reply_avatar_file = reply_profile.get("avatar", "default.png")
            reply_avatar_path = f"assets/avatars/{reply_avatar_file}"
            reply_avatar = AvatarLabel(reply_avatar_path, size=16)
            reply_name = QLabel(reply_profile.get("name", "Unknown"))
            reply_name.setStyleSheet("color: #eb459e; font-weight: bold; font-size: 10pt;")
            reply_text_str = reply_data.get("parts", [""])[0]
            if len(reply_text_str) > 40: reply_text_str = reply_text_str[:40] + "..."
            reply_text = QLabel(reply_text_str)
            reply_text.setStyleSheet("color: #b9bbbe; font-size: 10pt;")
            reply_banner_layout.addWidget(reply_avatar)
            reply_banner_layout.addWidget(reply_name)
            reply_banner_layout.addWidget(reply_text)
            reply_banner_layout.addStretch()
            main_vertical_layout.addWidget(reply_banner_widget)
            
        body_container = QWidget()
        body_layout = QHBoxLayout(body_container)
        body_layout.setContentsMargins(15, 1, 15, 1)
        body_layout.setSpacing(15)
        text_content_layout = QVBoxLayout()
        text_content_layout.setSpacing(2)
        if not is_grouped:
            avatar_path = f"assets/avatars/{profile.get('avatar', 'default.png')}"
            if not Path(avatar_path).exists(): avatar_path = "assets/avatars/default.png"
            avatar = AvatarLabel(avatar_path)
            body_layout.addWidget(avatar, 0, Qt.AlignTop)

            # --- NOVO LAYOUT PARA NOME + HORA ---
            name_time_layout = QHBoxLayout()
            name_time_layout.setSpacing(8)
            name_label = QLabel(name)
            name_label.setStyleSheet(f"color: {'#5865f2' if is_user else '#eb459e'}; font-weight: bold;")
            
            time_label = QLabel("")
            if timestamp_str:
                dt_object = datetime.fromisoformat(timestamp_str)
                time_label.setText(dt_object.strftime("%H:%M"))
            time_label.setStyleSheet("color: #96989d; font-size: 9pt;")
            
            name_time_layout.addWidget(name_label)
            name_time_layout.addWidget(time_label)
            name_time_layout.addStretch()
            text_content_layout.addLayout(name_time_layout)
        else:
            body_layout.addSpacing(55)
        if is_gif:
            gif_keyword = text_content.split(":", 1)[1].strip().split()[0]
            gif_path = f"assets/gifs/{gif_keyword}.gif"
            content_widget = QLabel()
            if Path(gif_path).exists():
                self.movie = QMovie(gif_path)
                content_widget.setMaximumSize(250, 200)
                content_widget.setScaledContents(True)
                content_widget.setMovie(self.movie)
                self.movie.start()
            else:
                content_widget.setText(f"[GIF '{gif_keyword}' não encontrado]")
                content_widget.setStyleSheet("color: #f04747;")
            text_content_layout.addWidget(content_widget)
        else:
            self.message_label = QLabel(text_content)
            self.message_label.setWordWrap(True)
            self.message_label.setObjectName("chat_message_label")
            self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            text_content_layout.addWidget(self.message_label)
        body_layout.addLayout(text_content_layout, 0 if is_gif else 100)
        body_layout.addStretch(1)
        if self.role == "model" and show_reply_button: # Adicione a condição aqui
            self.reply_button = QPushButton("↪")
            self.reply_button.setObjectName("replyButton")
            self.reply_button.setCursor(QCursor(Qt.PointingHandCursor))
            self.reply_button.setFixedSize(24, 24)
            self.reply_button.setVisible(False)
            self.reply_button.clicked.connect(lambda: self.reply_clicked.emit(self.message_data))
            self.setStyleSheet("QPushButton#replyButton { background-color: #40444b; border-radius: 4px; font-size: 14pt; color: #dcddde; }")
            body_layout.addWidget(self.reply_button, 0, Qt.AlignTop)
        main_vertical_layout.addWidget(body_container)

    def update_text(self, text):
        if hasattr(self, 'message_label'):
            self.message_label.setText(text)
    def enterEvent(self, event):
        if hasattr(self, 'reply_button'): self.reply_button.setVisible(True)
        super().enterEvent(event)
    def leaveEvent(self, event):
        if hasattr(self, 'reply_button'): self.reply_button.setVisible(False)
        super().leaveEvent(event)
class ServerButton(QPushButton):
    def __init__(self, server_data, parent=None):
        from pathlib import Path
        super().__init__("", parent); self.server_id = server_data["id"]; self.setObjectName("server_button"); self.setCheckable(True); self.setFixedSize(50, 50); self.set_server_icon(server_data); self.setContextMenuPolicy(Qt.CustomContextMenu)
    def set_server_icon(self, server_data):
        from pathlib import Path
        avatar_file = server_data.get("avatar"); avatar_path = f"assets/avatars/{avatar_file}"
        if avatar_file and Path(avatar_path).exists():
            source_pixmap = QPixmap(avatar_path); rounded = QPixmap(source_pixmap.size()); rounded.fill(Qt.transparent); painter = QPainter(rounded); painter.setRenderHint(QPainter.Antialiasing); path = QPainterPath(); path.addEllipse(0, 0, source_pixmap.width(), source_pixmap.height()); painter.setClipPath(path); painter.drawPixmap(0, 0, source_pixmap); painter.end(); icon = QIcon(rounded); self.setIcon(icon); self.setIconSize(QSize(40, 40)); self.setText("")
        else: self.setIcon(QIcon()); self.setText(server_data.get("name", "S")[0].upper())
class WelcomeWidget(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignCenter); self.label = QLabel(text); self.label.setObjectName("welcome_label"); self.label.setWordWrap(True); layout.addWidget(self.label)
class UIMixin:
    """Agrupa os métodos que criam as partes da interface."""
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
        if not avatar_path.exists(): avatar_path = self.assets_path / "default.png"
        self.user_panel_avatar = AvatarLabel(str(avatar_path), size=32); name_layout = QVBoxLayout(); name_layout.setSpacing(0)
        self.user_panel_name = QLabel(profile.get("name", "User")); self.user_panel_name.setObjectName("user_name_label")
        self.user_panel_id = QLabel(profile.get("id_tag", "#0000")); self.user_panel_id.setObjectName("user_id_label")
        name_layout.addWidget(self.user_panel_name); name_layout.addWidget(self.user_panel_id)
        
        # --- NOVOS BOTÕES ---
        # Botão para o player de filme
        self.movie_player_button = QPushButton("🎬") # Ícone de claquete
        self.movie_player_button.setObjectName("user_settings_button")
        self.movie_player_button.setToolTip("Abrir Sessão de Filme (LouFlix)")
        self.movie_player_button.clicked.connect(self._open_movie_player) # Conecta ao novo método

        # Botão para editar personalidade
        self.edit_personality_button = QPushButton("✏️") # Ícone de lápis
        self.edit_personality_button.setObjectName("user_settings_button")
        self.edit_personality_button.setToolTip("Editar Personalidade da Lou")
        self.edit_personality_button.clicked.connect(self._open_personality_editor)

        # Botão para configurações do usuário
        settings_button = QPushButton("⚙️"); settings_button.setObjectName("user_settings_button"); settings_button.clicked.connect(self.show_user_settings_dialog)
        
        layout.addWidget(self.user_panel_avatar)
        layout.addLayout(name_layout)
        layout.addStretch()
        layout.addWidget(self.movie_player_button) # Adiciona o botão novo
        layout.addWidget(self.edit_personality_button)
        layout.addWidget(settings_button)
        return panel
    def create_chat_panel(self):
        panel = QFrame(); panel.setObjectName("chat_panel"); layout = QVBoxLayout(panel); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0); top_bar = QFrame(); top_bar.setObjectName("chat_top_bar"); top_bar_layout = QHBoxLayout(top_bar)
        self.chat_channel_name_label = QLabel("..."); self.chat_channel_name_label.setObjectName("chat_channel_name"); top_bar_layout.addWidget(self.chat_channel_name_label); top_bar_layout.addStretch()
        layout.addWidget(top_bar)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True); self.scroll_area.setObjectName("chat_scroll_area"); self.chat_container = QWidget(); self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch(); self.scroll_area.setWidget(self.chat_container); layout.addWidget(self.scroll_area, 1); self.chat_layout.setContentsMargins(10, 10, 10, 20)
        input_area_widget = QWidget()
        input_area_layout = QVBoxLayout(input_area_widget)
        input_area_layout.setContentsMargins(15, 10, 15, 20)
        input_area_layout.setSpacing(0)
        self.reply_indicator = ReplyIndicatorWidget(self.data.get("profiles", {}))
        self.reply_indicator.reply_cancelled.connect(self._handle_reply_cancelled)
        input_frame = QFrame(); input_frame.setObjectName("chat_input_frame"); input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        self.text_input = ChatInput(); self.text_input.sendMessage.connect(self.on_message_sent)
        input_layout.addWidget(self.text_input)
        input_area_layout.addWidget(self.reply_indicator)
        input_area_layout.addWidget(input_frame)
        layout.addWidget(input_area_widget)
        return panel
    def load_stylesheet(self):
        c_dark_heavy="#202225";c_dark_medium="#2f3136";c_dark_light="#36393f";c_dark_lighter="#40444b";c_text_header="#72767d";c_text_normal="#dcddde";c_text_active="#ffffff";c_brand="#5865f2"
        return f""" QMainWindow{{background-color:{c_dark_heavy};}} QFrame#server_list{{background-color:{c_dark_heavy};}} QPushButton#server_button{{background-color:{c_dark_light};color:{c_text_normal};font-size:16pt;font-weight:bold;border:none;border-radius:25px;padding:0;}} QPushButton#server_button:hover{{border-radius:15px;}} QPushButton#server_button:checked{{background-color:{c_brand};border-radius:15px;}} QPushButton#server_action_button{{background-color:{c_dark_light};color:#23a55a;font-size:20pt;border:none;border-radius:25px;height:50px;width:50px; padding-bottom: 4px;}} QPushButton#server_action_button:hover{{background-color:#23a55a;color:{c_text_active};border-radius:15px;}} QSplitter::handle{{background-color:#282a2e;}} QFrame#channel_panel{{background-color:{c_dark_medium};}} QLabel#server_name_label{{color:{c_text_active};font-weight:bold;padding:20px 15px;border-bottom:1px solid {c_dark_heavy};}} QLabel#server_name_label:hover{{background-color:{c_dark_lighter};}} QScrollArea{{border:none;}} QLabel#channel_header{{color:{c_text_header};font-size:9pt;font-weight:bold;}} QLabel#no_channels_label{{color:{c_text_header};font-style:italic;padding:8px;}} QLabel#welcome_label {{ color:{c_text_active}; font-size: 16pt; font-weight: bold; text-align: center; }} QPushButton#add_channel_button{{color:{c_text_header};font-size:14pt;font-weight:bold;border:none;border-radius:10px;text-align:center;}} QPushButton#add_channel_button:hover{{color:{c_text_active};}} QPushButton#channel_button,QPushButton#channel_button_active{{color:{c_text_header};text-align:left;padding:8px;border-radius:4px;font-size:11pt;border:none;}} QPushButton#channel_button:hover{{background-color:{c_dark_lighter};color:{c_text_normal};}} QPushButton#channel_button:checked,QPushButton#channel_button_active{{background-color:{c_dark_lighter};color:{c_text_active};}} QFrame#user_panel{{background-color:#232428;padding:5px;}} QLabel#user_name_label{{color:{c_text_active};font-weight:bold;font-size:10pt;}} QLabel#user_id_label{{color:{c_text_header};font-size:8pt;}} QPushButton#user_settings_button {{ color:{c_text_header};border:none;font-size:11pt;border-radius:4px;width:24px;height:24px;}} QPushButton#user_settings_button:hover {{ color:{c_text_active};background-color:{c_dark_lighter};}} QFrame#chat_panel{{background-color:{c_dark_light};}} QFrame#chat_top_bar{{border-bottom:1px solid {c_dark_heavy};padding:12px 15px;}} QLabel#chat_channel_name{{color:{c_text_active};font-weight:bold;font-size:12pt;}} QScrollArea#chat_scroll_area{{border:none;}} QFrame#chat_input_frame{{padding:0; border-radius: 8px; background-color: {c_dark_lighter};}} ChatInput{{background-color:transparent;border:none;border-radius:8px;font-size:11pt;padding:10px 15px;color:{c_text_normal};}} QLabel#chat_message_label {{ color: {c_text_normal}; font-size: 11pt; }} QFrame#message_widget {{ min-height: 20px; }} QScrollBar:vertical{{border:none;background:{c_dark_medium};width:8px;margin:0;}} QScrollBar::handle:vertical{{background:{c_dark_heavy};min-height:20px;border-radius:4px;}} QMenu {{ background-color: {c_dark_heavy}; color: {c_text_normal}; border: 1px solid #1a1b1e; }} QMenu::item:selected {{ background-color: {c_brand}; }} QMenu::item#deleteAction {{ color: #d83c3e; }} """

class DateSeparatorWidget(QFrame):
    """Um widget para exibir uma linha separadora de data no chat."""
    def __init__(self, date_str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setAlignment(Qt.AlignCenter)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet("border: 1px solid #40444b;")

        self.label = QLabel(date_str)
        self.label.setStyleSheet("color: #96989d; font-size: 9pt; font-weight: bold; padding: 0 10px;")

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("border: 1px solid #40444b;")
        
        layout.addWidget(line1)
        layout.addWidget(self.label)
        layout.addWidget(line2)

class InfoDialog(BaseDialog):
    """Um diálogo customizado para exibir informações ou avisos."""
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel(title)
        self.label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-bottom: 5px;")
        
        self.message = QLabel(message)
        self.message.setWordWrap(True)
        
        self.buttons = QHBoxLayout()
        self.ok_button = QPushButton("Ok")
        self.ok_button.setObjectName("primaryButton")
        self.ok_button.clicked.connect(self.accept)
        
        self.buttons.addStretch()
        self.buttons.addWidget(self.ok_button)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.message)
        self.layout.addLayout(self.buttons)        