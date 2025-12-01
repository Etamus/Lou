# LouMain.py
import sys
import random
import json
import re
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QMessageBox
from PySide6.QtCore import QTimer

from LouFE import UIMixin, WelcomeWidget
from LouBE import AppLogicMixin
from LouIAFE import AIFeaturesMixin
from LouEditor import PersonalityEditorWindow # <-- ALTERAÇÃO AQUI
from LouFlix import MoviePlayerWindow

class LouApp(QMainWindow, AppLogicMixin, UIMixin, AIFeaturesMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lou"); self.setGeometry(100, 100, 1280, 720)
        self.assets_path = Path("assets/avatars"); self.assets_path.mkdir(parents=True, exist_ok=True)
        self.gifs_path = Path("assets/gifs"); self.gifs_path.mkdir(parents=True, exist_ok=True)
        self.data_path = Path("data"); self.data_path.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_path / "chat_data.json"
        self.memory_file = self.data_path / "memory_bank.json"
        self.style_file = self.data_path / "style_bank.json"
        self.personality_file = self.data_path / "personality_prompt.json"
        self.data = {}; self.long_term_memories = []; self.short_term_memories = []
        self.style_patterns = []; self.personality_data = {}; self.server_buttons = {}
        self.channel_buttons = {}; self.current_server_id = None; self.current_channel_id = None
        self.current_reply_context = None; self.gemini_model = None; self.worker = None
        self.context_update_worker = None; self.proactive_worker = None; self.current_ai_message_widget = None
        self.current_ai_raw_text = ""; self.proactive_attempts = 0
        self.available_gifs = [p.stem for p in self.gifs_path.glob("*.gif")]; self.has_mentioned_late_hour = False
        self._prompt_override = None
        self.inactivity_timer = QTimer(self); self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.send_proactive_message)
        self.debounce_timer = QTimer(self); self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.start_ai_response)
        try:
            with open(self.personality_file, "r", encoding="utf-8") as f:
                self.personality_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"### ERRO CRÍTICO: Não foi possível carregar o arquivo de personalidade: {e} ###")
            self.personality_data = {}
        self.setStyleSheet(self.load_stylesheet())
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget); self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0); self.setup_gemini_model()
        self.WelcomeWidget = WelcomeWidget; self.setup_data_and_ui()

    def _open_personality_editor(self):
        editor = PersonalityEditorWindow(self.personality_file, self)
        editor.personality_saved.connect(self._reload_personality)
        editor.exec()

    # Adicione este novo método
    def _open_movie_player(self):
        # Passamos 'self' para que a nova janela tenha acesso ao modelo, dados, etc.
        player_window = MoviePlayerWindow(self, self) 
        player_window.exec() # .exec() para abrir como um diálogo modal        

    def _reload_personality(self):
        print("--- Personalidade alterada. Recarregando modelo da IA... ---")
        try:
            with open(self.personality_file, "r", encoding="utf-8") as f:
                self.personality_data = json.load(f)
            self.setup_gemini_model()
            self.refresh_user_panels()
            print("--- Modelo da IA recarregado com sucesso. ---")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"### ERRO AO RECARREGAR PERSONALIDADE: {e} ###")
            QMessageBox.critical(self, "Erro", "Não foi possível recarregar o arquivo de personalidade.")

    def closeEvent(self, event):
        self.stop_ai_worker_safely()
        try:
            if hasattr(self, 'context_update_worker') and self.context_update_worker and self.context_update_worker.isRunning():
                self.context_update_worker.wait_for_finish()
        except RuntimeError: pass
        try:
            if hasattr(self, 'proactive_worker') and self.proactive_worker and self.proactive_worker.isRunning():
                self.proactive_worker.wait_for_finish()
        except RuntimeError: pass
        self.save_data()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LouApp()
    window.show()
    sys.exit(app.exec())