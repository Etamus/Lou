from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QScrollArea, QLabel,
    QFrame, QSplitter, QDialog, QLineEdit, QFileDialog, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import (
    QFont, QKeyEvent, QPainter, QPen, QColor, QIcon, QCursor, QPixmap, QPainterPath, QAction
)

# --- DIÁLOGOS DE CONFIGURAÇÃO ---
class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet("QDialog { background-color: #36393f; color: #dcddde; border: 1px solid #282a2e; } QLabel#dialog_label { color: #b9bbbe; font-size: 9pt; font-weight: bold; } QLineEdit#dialog_input { background-color: #202225; color: #dcddde; border: 1px solid #202225; border-radius: 3px; padding: 8px; } QPushButton { background-color: #4f545c; color: #fff; border: none; padding: 8px 16px; border-radius: 3px; font-weight: bold;} QPushButton:hover { background-color: #5d636b; }")

class RenameDialog(BaseDialog):
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self); self.label = QLabel("NOME DO CANAL"); self.label.setObjectName("dialog_label"); self.input = QLineEdit(current_name); self.input.setObjectName("dialog_input"); self.buttons = QHBoxLayout(); self.ok_button = QPushButton("Renomear"); self.ok_button.clicked.connect(self.accept); self.buttons.addStretch(); self.buttons.addWidget(self.ok_button); self.layout.addWidget(self.label); self.layout.addWidget(self.input); self.layout.addLayout(self.buttons)
    def get_new_name(self): return self.input.text().strip()

class ConfirmationDialog(BaseDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self); self.label = QLabel(title); self.label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-bottom: 5px;"); self.message = QLabel(message); self.message.setWordWrap(True); self.buttons = QHBoxLayout(); self.no_button = QPushButton("Não"); self.no_button.clicked.connect(self.reject); self.yes_button = QPushButton("Sim"); self.yes_button.clicked.connect(self.accept); self.yes_button.setStyleSheet("background-color: #d83c3e;"); self.buttons.addStretch(); self.buttons.addWidget(self.no_button); self.buttons.addWidget(self.yes_button); self.layout.addWidget(self.label); self.layout.addWidget(self.message); self.layout.addLayout(self.buttons)

class CreateChannelDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout=QVBoxLayout(self); self.name_label = QLabel("NOME DO CANAL"); self.name_label.setObjectName("dialog_label"); self.input = QLineEdit(); self.input.setObjectName("dialog_input"); self.buttons = QHBoxLayout(); self.ok_button = QPushButton("Criar"); self.ok_button.clicked.connect(self.accept); self.buttons.addStretch(); self.buttons.addWidget(self.ok_button); self.layout.addWidget(self.name_label); self.layout.addWidget(self.input); self.layout.addLayout(self.buttons)
    def get_channel_name(self): return self.input.text().strip()

class ServerSettingsDialog(BaseDialog):
    def __init__(self, current_name, current_avatar_path, parent=None):
        super().__init__(parent)
        self.new_avatar_path = None; self.layout = QVBoxLayout(self); self.avatar_label = AvatarLabel(current_avatar_path, size=80); change_avatar_button = QPushButton("Alterar ícone"); change_avatar_button.clicked.connect(self.change_avatar); self.label = QLabel("NOME DO SERVIDOR"); self.label.setObjectName("dialog_label"); self.input = QLineEdit(current_name); self.input.setObjectName("dialog_input"); self.buttons = QHBoxLayout(); self.delete_button = QPushButton("Excluir"); self.delete_button.setStyleSheet("background-color: #d83c3e;"); self.save_button = QPushButton("Salvar"); self.save_button.clicked.connect(self.accept); self.buttons.addWidget(self.delete_button); self.buttons.addStretch(); self.buttons.addWidget(self.save_button); self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter); self.layout.addWidget(change_avatar_button); self.layout.addWidget(self.label); self.layout.addWidget(self.input); self.layout.addLayout(self.buttons)
    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone do Servidor", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.new_avatar_path = file_path
            self.avatar_label.set_avatar(file_path)
    def get_values(self): return {"name": self.input.text().strip(), "avatar_path": self.new_avatar_path}

class CreateServerDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_avatar_path = None; self.layout = QVBoxLayout(self); self.avatar_label = AvatarLabel("assets/avatars/default_server.png", size=80); self.avatar_button = QPushButton("Enviar Ícone"); self.avatar_button.clicked.connect(self.change_avatar); self.name_label = QLabel("NOME DO SERVIDOR"); self.name_label.setObjectName("dialog_label"); self.name_input = QLineEdit(); self.name_input.setObjectName("dialog_input"); self.name_input.setPlaceholderText("Ex: Clube de Games"); self.buttons = QHBoxLayout(); self.ok_button = QPushButton("Criar"); self.ok_button.clicked.connect(self.accept); self.buttons.addStretch(); self.buttons.addWidget(self.ok_button); self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter); self.layout.addWidget(self.avatar_button); self.layout.addWidget(self.name_label); self.layout.addWidget(self.name_input); self.layout.addLayout(self.buttons)
    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Ícone do Servidor", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.new_avatar_path = file_path
            self.avatar_label.set_avatar(file_path)
    def get_values(self): return {"name": self.name_input.text().strip(), "avatar_path": self.new_avatar_path}

class UserSettingsDialog(BaseDialog):
    def __init__(self, current_name, current_avatar_path, parent=None):
        super().__init__(parent)
        self.new_avatar_path = None; self.layout = QVBoxLayout(self); self.avatar_label = AvatarLabel(current_avatar_path, 80); change_avatar_button = QPushButton("Alterar avatar"); change_avatar_button.clicked.connect(self.change_avatar); self.name_label = QLabel("NOME DE USUÁRIO"); self.name_label.setObjectName("dialog_label"); self.name_input = QLineEdit(current_name); self.name_input.setObjectName("dialog_input"); self.buttons = QHBoxLayout(); self.save_button = QPushButton("Salvar"); self.save_button.clicked.connect(self.accept); self.buttons.addStretch(); self.buttons.addWidget(self.save_button); self.layout.addWidget(self.avatar_label, 0, Qt.AlignCenter); self.layout.addWidget(change_avatar_button); self.layout.addWidget(self.name_label); self.layout.addWidget(self.name_input); self.layout.addLayout(self.buttons)
    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Avatar", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.new_avatar_path = file_path
            self.avatar_label.set_avatar(file_path)
    def get_values(self): return {"name": self.name_input.text().strip(), "avatar_path": self.new_avatar_path}

# --- WIDGETS CUSTOMIZADOS ---
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

class AvatarLabel(QLabel):
    def __init__(self, avatar_path, size=40, parent=None): super().__init__(parent); self.setFixedSize(size, size); self.set_avatar(avatar_path)
    def set_avatar(self, avatar_path):
        pixmap = QPixmap(avatar_path)
        if pixmap.isNull(): pixmap = QPixmap("assets/avatars/default.png")
        rounded = QPixmap(pixmap.size()); rounded.fill(Qt.transparent); painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing); path = QPainterPath(); path.addEllipse(0, 0, pixmap.width(), pixmap.height())
        painter.setClipPath(path); painter.drawPixmap(0, 0, pixmap); painter.end()
        self.setPixmap(rounded.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

class ChatMessageWidget(QFrame):
    def __init__(self, message_data, profiles, is_grouped=False, parent=None):
        from pathlib import Path
        super().__init__(parent); self.setObjectName("message_widget"); self.role = message_data.get("role", "user"); is_user = self.role == "user"; profile = profiles.get(self.role, {}); avatar_file = profile.get("avatar", "default.png"); avatar_path = f"assets/avatars/{avatar_file}"
        if not Path(avatar_path).exists(): avatar_path = "assets/avatars/default.png"
        name = profile.get("name", "Unknown"); text = message_data.get("parts", [""])[0]; layout = QHBoxLayout(self); layout.setContentsMargins(15, 1, 15, 1); layout.setSpacing(15)
        if not is_grouped:
            layout.setContentsMargins(15, 10, 15, 1); avatar = AvatarLabel(avatar_path); text_content_layout = QVBoxLayout(); text_content_layout.setSpacing(2); name_label = QLabel(name); name_label.setObjectName("chat_name_label"); name_label.setStyleSheet(f"color: {'#5865f2' if is_user else '#eb459e'}; font-weight: bold;"); self.message_label = QLabel(text); self.message_label.setWordWrap(True); self.message_label.setObjectName("chat_message_label"); self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse); text_content_layout.addWidget(name_label); text_content_layout.addWidget(self.message_label); layout.addWidget(avatar, 0, Qt.AlignTop); layout.addLayout(text_content_layout, 1)
        else:
            self.message_label = QLabel(text); self.message_label.setWordWrap(True); self.message_label.setObjectName("chat_message_label"); self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse); layout.addSpacing(55); layout.addWidget(self.message_label, 1)
    def update_text(self, text): self.message_label.setText(text)

class ServerButton(QPushButton):
    def __init__(self, server_data, parent=None):
        from pathlib import Path
        super().__init__("", parent); self.server_id = server_data["id"]; self.setObjectName("server_button"); self.setCheckable(True); self.setFixedSize(50, 50); self.set_server_icon(server_data); self.setContextMenuPolicy(Qt.CustomContextMenu)
    def set_server_icon(self, server_data):
        from pathlib import Path
        avatar_file = server_data.get("avatar"); avatar_path = f"assets/avatars/{avatar_file}"
        if avatar_file and Path(avatar_path).exists():
            source_pixmap = QPixmap(avatar_path); rounded = QPixmap(source_pixmap.size()); rounded.fill(Qt.transparent); painter = QPainter(rounded); painter.setRenderHint(QPainter.Antialiasing); path = QPainterPath(); path.addEllipse(0, 0, source_pixmap.width(), source_pixmap.height()); painter.setClipPath(path); painter.drawPixmap(0, 0, source_pixmap); painter.end(); icon = QIcon(rounded); self.setIcon(icon); self.setIconSize(QSize(40, 40)); self.setText("")
        else:
            self.setIcon(QIcon()); self.setText(server_data.get("name", "S")[0].upper())

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

    def load_stylesheet(self):
        c_dark_heavy="#202225";c_dark_medium="#2f3136";c_dark_light="#36393f";c_dark_lighter="#40444b";c_text_header="#72767d";c_text_normal="#dcddde";c_text_active="#ffffff";c_brand="#5865f2"
        return f""" QMainWindow{{background-color:{c_dark_heavy};}} QFrame#server_list{{background-color:{c_dark_heavy};}} QPushButton#server_button{{background-color:{c_dark_light};color:{c_text_normal};font-size:16pt;font-weight:bold;border:none;border-radius:25px;padding:0;}} QPushButton#server_button:hover{{border-radius:15px;}} QPushButton#server_button:checked{{background-color:{c_brand};border-radius:15px;}} QPushButton#server_action_button{{background-color:{c_dark_light};color:#23a55a;font-size:20pt;border:none;border-radius:25px;height:50px;width:50px;}} QPushButton#server_action_button:hover{{background-color:#23a55a;color:{c_text_active};border-radius:15px;}} QSplitter::handle{{background-color:#282a2e;}} QFrame#channel_panel{{background-color:{c_dark_medium};}} QLabel#server_name_label{{color:{c_text_active};font-weight:bold;padding:20px 15px;border-bottom:1px solid {c_dark_heavy};}} QLabel#server_name_label:hover{{background-color:{c_dark_lighter};}} QScrollArea{{border:none;}} QLabel#channel_header{{color:{c_text_header};font-size:9pt;font-weight:bold;}} QLabel#no_channels_label{{color:{c_text_header};font-style:italic;padding:8px;}} QLabel#welcome_label {{ color:{c_text_active}; font-size: 16pt; font-weight: bold; text-align: center; }} QPushButton#add_channel_button{{color:{c_text_header};font-size:14pt;font-weight:bold;border:none;border-radius:10px;text-align:center;}} QPushButton#add_channel_button:hover{{color:{c_text_active};}} QPushButton#channel_button,QPushButton#channel_button_active{{color:{c_text_header};text-align:left;padding:8px;border-radius:4px;font-size:11pt;border:none;}} QPushButton#channel_button:hover{{background-color:{c_dark_lighter};color:{c_text_normal};}} QPushButton#channel_button:checked,QPushButton#channel_button_active{{background-color:{c_dark_lighter};color:{c_text_active};}} QFrame#user_panel{{background-color:#232428;padding:5px;}} QLabel#user_name_label{{color:{c_text_active};font-weight:bold;font-size:10pt;}} QLabel#user_id_label{{color:{c_text_header};font-size:8pt;}} QPushButton#user_settings_button {{ color:{c_text_header};border:none;font-size:11pt;border-radius:4px;width:24px;height:24px;}} QPushButton#user_settings_button:hover {{ color:{c_text_active};background-color:{c_dark_lighter};}} QFrame#chat_panel{{background-color:{c_dark_light};}} QFrame#chat_top_bar{{border-bottom:1px solid {c_dark_heavy};padding:12px 15px;}} QLabel#chat_channel_name{{color:{c_text_active};font-weight:bold;font-size:12pt;}} QScrollArea#chat_scroll_area{{border:none;}} QFrame#chat_input_frame{{padding:0 15px 20px 15px;}} ChatInput{{background-color:{c_dark_lighter};border:none;border-radius:8px;font-size:11pt;padding:10px 15px;color:{c_text_normal};}} QLabel#chat_message_label {{ color: {c_text_normal}; font-size: 11pt; }} QFrame#message_widget {{ min-height: 20px; }} QScrollBar:vertical{{border:none;background:{c_dark_medium};width:8px;margin:0;}} QScrollBar::handle:vertical{{background:{c_dark_heavy};min-height:20px;border-radius:4px;}} QMenu {{ background-color: {c_dark_heavy}; color: {c_text_normal}; border: 1px solid #1a1b1e; }} QMenu::item:selected {{ background-color: {c_brand}; }} QMenu::item#deleteAction {{ color: #d83c3e; }} """