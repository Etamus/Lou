import json
import uuid
import shutil
import random
from pathlib import Path
from functools import partial
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QMenu
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction

from LouFE import (
    RenameDialog, ConfirmationDialog, CreateChannelDialog, ServerSettingsDialog,
    CreateServerDialog, UserSettingsDialog, ServerButton
)

class AppLogicMixin:
    """Agrupa a lógica de negócios e o gerenciamento de dados do aplicativo."""

    def setup_data_and_ui(self):
        self.load_or_create_data()
        if self.data["servers"]:
            if not self.current_server_id or self.current_server_id not in [s['id'] for s in self.data['servers']]:
                self.current_server_id = self.data["servers"][0]["id"]
            server = self.get_current_server()
            if server and server["channels"]:
                text_channels = [c for c in server['channels'] if c.get('type') == 'text']
                if text_channels: self.current_channel_id = text_channels[0]['id']

        self.welcome_widget = self.WelcomeWidget("Crie ou selecione um servidor para começar.")
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
        if "profiles" not in self.data: self.data["profiles"] = {"user":{"name":"Mateus","id_tag":"#1987","avatar":"default.png"},"model":{"name":"Lou","id_tag":"#AI","avatar":"lou.png"}}
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
                if isinstance(mem, str) and mem not in self.long_term_memory: self.long_term_memory.append(mem)
            with open(self.memory_file, "w", encoding="utf-8") as f: json.dump(self.long_term_memory, f, indent=4, ensure_ascii=False)

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
            button = ServerButton(server); button.clicked.connect(partial(self.on_server_button_clicked, server["id"])); button.customContextMenuRequested.connect(partial(self.show_server_context_menu, button.server_id)); self.server_list_layout.addWidget(button, 0, Qt.AlignCenter); self.server_buttons[server["id"]] = button

        add_server_button = QPushButton("+"); add_server_button.setObjectName("server_action_button"); add_server_button.clicked.connect(self.show_create_server_dialog)
        self.server_list_layout.addWidget(add_server_button, 0, Qt.AlignCenter)
        self.server_list_layout.addStretch(1)

    def populate_channel_list(self):
        while self.channels_layout.count() > 1: item = self.channels_layout.takeAt(0);_=[w.deleteLater() for w in [item.widget()] if w]
        self.channel_buttons.clear(); server = self.get_current_server()
        if not server: self.server_name_label.setText("Nenhum Servidor"); return
        self.server_name_label.setText(server["name"]); text_channels = [c for c in server["channels"] if c.get("type") == "text"]; header_widget = QWidget(); header_layout = QHBoxLayout(header_widget); header_layout.setContentsMargins(0,0,0,0); text_header = QLabel("CANAIS DE TEXTO"); text_header.setObjectName("channel_header"); add_channel_button = QPushButton("+"); add_channel_button.setObjectName("add_channel_button"); add_channel_button.setFixedSize(20,20); add_channel_button.clicked.connect(self.show_create_channel_dialog); header_layout.addWidget(text_header); header_layout.addStretch(); header_layout.addWidget(add_channel_button); self.channels_layout.insertWidget(self.channels_layout.count() - 1, header_widget)
        if not text_channels: no_channels_label = QLabel("Nenhum canal de texto"); no_channels_label.setObjectName("no_channels_label"); self.channels_layout.insertWidget(self.channels_layout.count()-1, no_channels_label)
        for channel in text_channels:
            button = QPushButton(f"# {channel['name']}"); button.setObjectName("channel_button"); button.setCheckable(True); button.clicked.connect(partial(self.on_channel_button_clicked, channel["id"])); button.setContextMenuPolicy(Qt.CustomContextMenu); button.customContextMenuRequested.connect(partial(self.show_channel_context_menu, channel["id"])); self.channels_layout.insertWidget(self.channels_layout.count() - 1, button); self.channel_buttons[channel["id"]] = button

    def populate_chat_messages(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        channel = self.get_current_channel()
        if not channel:
            self.chat_channel_name_label.setText(""); self.text_input.set_placeholder_text("Crie um canal para começar"); self.text_input.setEnabled(False)
            return
        self.text_input.setEnabled(True); self.chat_channel_name_label.setText(f"# {channel['name']}"); self.text_input.set_placeholder_text(f"Conversar em #{channel['name']}")
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
        history = self.get_current_channel_history(); history_copy = [msg for msg in history if msg.get("parts") and msg.get("parts")[0]]; user_name = self.data.get("profiles", {}).get("user", {}).get("name", "Pai"); history_copy.insert(0, {"role": "user", "parts": [f"[Contexto: O nome do seu pai é '{user_name}'.]"]}); 
        if self.long_term_memory:
            sample_size = min(len(self.long_term_memory), 3); random_memories = __import__('random').sample(self.long_term_memory, sample_size)
            history_copy.insert(1, {"role": "user", "parts": [f"[Lembretes de memória: {' | '.join(random_memories)}]"]})
        return history_copy

    def show_channel_context_menu(self, channel_id, pos):
        channel = next((c for s in self.data["servers"] if s["id"] == self.current_server_id for c in s["channels"] if c["id"] == channel_id), None); 
        if not channel: return
        menu = QMenu(self); rename_action = QAction("Renomear", self); delete_action = QAction("Excluir", self); delete_action.setObjectName("deleteAction"); menu.setStyleSheet(self.load_stylesheet()); rename_action.triggered.connect(lambda: self.rename_channel(channel_id)); delete_action.triggered.connect(lambda: self.delete_channel(channel_id)); menu.addAction(rename_action); menu.addSeparator(); menu.addAction(delete_action)
        if button := self.channel_buttons.get(channel_id): menu.exec(button.mapToGlobal(pos))

    def rename_channel(self, channel_id):
        server = self.get_current_server(); 
        if not server: return
        channel = next((c for c in server["channels"] if c["id"] == channel_id), None); 
        if not channel: return
        dialog = RenameDialog(channel["name"], self)
        if dialog.exec():
            new_name = dialog.get_new_name()
            if new_name and new_name.strip() and new_name.strip() != channel["name"]:
                channel["name"] = new_name.strip(); self.save_data(); self.populate_channel_list()
                if self.current_channel_id == channel_id: self.populate_chat_messages()
                self.update_active_buttons()

    def delete_channel(self, channel_id):
        server_of_channel = next((s for s in self.data["servers"] if any(c["id"] == channel_id for c in s["channels"])), None); 
        if not server_of_channel: return
        channel = next((c for c in server_of_channel["channels"] if c["id"] == channel_id), None); 
        if not channel: return
        if len([c for c in server_of_channel["channels"] if c.get("type") == "text"]) <= 1:
            QMessageBox.warning(self, "Aviso", "Não é possível excluir o único canal de texto do servidor."); return
        dialog = ConfirmationDialog("Excluir Canal", f"Você tem certeza que quer excluir o canal '{channel['name']}'?", self)
        if dialog.exec():
            server_of_channel["channels"] = [c for c in server_of_channel["channels"] if c["id"] != channel_id]; self.save_data()
            if self.current_channel_id == channel_id:
                text_channels = [c for c in server_of_channel["channels"] if c.get("type") == "text"]
                self.current_channel_id = text_channels[0]["id"] if text_channels else None
            self.populate_all_ui()

    def show_server_context_menu(self, server_id, pos):
        server = next((s for s in self.data["servers"] if s["id"] == server_id), None); 
        if not server: return
        menu = QMenu(self); settings_action = QAction("Configurações", self); delete_action = QAction("Excluir", self); delete_action.setObjectName("deleteAction"); menu.setStyleSheet(self.load_stylesheet()); settings_action.triggered.connect(lambda: self.show_server_settings_dialog(server_id)); delete_action.triggered.connect(lambda: self.delete_server(server_id)); menu.addAction(settings_action); menu.addSeparator(); menu.addAction(delete_action)
        if button := self.server_buttons.get(server_id): menu.exec(button.mapToGlobal(pos))

    def show_create_channel_dialog(self):
        dialog = CreateChannelDialog(self)
        if dialog.exec():
            channel_name = dialog.get_channel_name()
            if channel_name:
                if server := self.get_current_server():
                    new_channel = {"id": f"c_{uuid.uuid4().hex[:6]}", "name": channel_name, "type": "text", "messages": []}; server["channels"].append(new_channel); self.save_data(); self.populate_channel_list(); self.on_channel_button_clicked(new_channel["id"])

    def show_server_settings_dialog(self, server_id_to_edit=None):
        server_id = server_id_to_edit if server_id_to_edit else self.current_server_id
        server = next((s for s in self.data["servers"] if s["id"] == server_id), None); 
        if not server: return
        avatar_filename = server.get("avatar") or "default_server.png"; avatar_path = str(self.assets_path / avatar_filename)
        dialog = ServerSettingsDialog(server["name"], avatar_path, self)
        dialog.delete_button.clicked.connect(lambda: self.delete_server(server_id))
        if dialog.exec():
            values = dialog.get_values(); changed = False
            if values["name"] and values["name"] != server["name"]: server["name"] = values["name"]; changed = True
            if values["avatar_path"]: new_path = Path(values["avatar_path"]); new_filename = f"{uuid.uuid4().hex}{new_path.suffix}"; shutil.copy(new_path, self.assets_path / new_filename); server["avatar"] = new_filename; changed = True
            if changed:
                self.save_data(); self.populate_server_list(); self.update_active_buttons()
                if server["id"] == self.current_server_id: self.server_name_label.setText(server["name"])

    def delete_server(self, server_id):
        server = next((s for s in self.data["servers"] if s["id"] == server_id), None); 
        if not server: return
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmationDialog) or isinstance(widget, ServerSettingsDialog): widget.reject()
        dialog = ConfirmationDialog("Excluir Servidor", f"Você tem certeza que quer excluir o servidor '{server['name']}'?", self)
        if dialog.exec():
            self.data["servers"] = [s for s in self.data["servers"] if s["id"] != server_id]; self.save_data()
            if self.current_server_id == server_id:
                if self.data["servers"]: self.on_server_button_clicked(self.data["servers"][0]["id"])
                else: self.current_server_id = None; self.current_channel_id = None
            self.populate_all_ui()

    def show_create_server_dialog(self):
        dialog = CreateServerDialog(self)
        if dialog.exec():
            values = dialog.get_values()
            if values["name"]:
                new_server = {"id": f"s_{uuid.uuid4().hex[:6]}", "name": values["name"], "icon_char": values["name"][0], "avatar": None, "channels": [{"id": f"c_{uuid.uuid4().hex[:6]}", "name": "geral", "type": "text", "messages": []}]}
                if values["avatar_path"]: new_path = Path(values["avatar_path"]); new_filename = f"{uuid.uuid4().hex}{new_path.suffix}"; shutil.copy(new_path, self.assets_path / new_filename); new_server["avatar"] = new_filename
                self.data["servers"].append(new_server); self.save_data(); self.populate_server_list(); self.on_server_button_clicked(new_server["id"])

    def show_user_settings_dialog(self):
        profile = self.data["profiles"]["user"]; avatar_path = str(self.assets_path / profile.get("avatar", "default.png"))
        dialog = UserSettingsDialog(profile["name"], avatar_path, self)
        if dialog.exec():
            values = dialog.get_values()
            if values["name"] and values["name"] != profile["name"]: profile["name"] = values["name"]
            if values["avatar_path"]: new_path = Path(values["avatar_path"]); new_filename = f"{uuid.uuid4().hex}{new_path.suffix}"; shutil.copy(new_path, self.assets_path / new_filename); profile["avatar"] = new_filename
            self.save_data(); self.refresh_user_panels()

    def refresh_user_panels(self):
        profile = self.data["profiles"]["user"]; avatar_path = self.assets_path / profile.get("avatar", "default.png")
        if not avatar_path.exists(): avatar_path = self.assets_path / "default.png"
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

    def update_active_buttons(self):
        for sid,btn in self.server_buttons.items(): btn.setChecked(sid == self.current_server_id)
        for cid,btn in self.channel_buttons.items():
            is_active = (cid == self.current_channel_id); btn.setChecked(is_active); btn.setObjectName("channel_button_active" if is_active else "channel_button"); btn.style().unpolish(btn); btn.style().polish(btn)

    def stop_ai_worker_safely(self):
        self.inactivity_timer.stop()
        if self.worker is not None:
            if self.worker.isRunning(): self.worker.wait_for_finish()
            self.worker = None