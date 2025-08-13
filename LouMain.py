# LouMain.py
import sys
import random
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PySide6.QtCore import QTimer

# Importa as funcionalidades de cada módulo especializado
from LouFE import UIMixin, WelcomeWidget
from LouBE import AppLogicMixin
from LouIAFE import AIFeaturesMixin

class LouApp(QMainWindow, AppLogicMixin, UIMixin, AIFeaturesMixin):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lou")
        self.setGeometry(100, 100, 1280, 720)

        # --- Variáveis de Estado da Aplicação ---
        self.assets_path = Path("assets/avatars")
        self.assets_path.mkdir(parents=True, exist_ok=True)
        self.gifs_path = Path("assets/gifs")
        self.gifs_path.mkdir(parents=True, exist_ok=True)        
        self.data_path = Path("data")
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_path / "chat_data.json"
        self.memory_file = self.data_path / "memory_bank.json" # Reativado
        self.style_file = self.data_path / "style_bank.json"   # Reativado
        
        self.data = {}
        self.long_term_memory = [] # Reativado
        self.style_patterns = []   # Reativado
        self.server_buttons = {}
        self.channel_buttons = {}
        self.current_server_id = None
        self.current_channel_id = None
        self.current_reply_context = None

        # --- Variáveis de Estado da IA ---
        self.gemini_model = None
        self.worker = None
        self.context_update_worker = None # Novo worker unificado
        self.proactive_worker = None
        self.current_ai_message_widget = None
        self.current_ai_raw_text = ""
        self.proactive_attempts = 0
        self.available_gifs = [p.stem for p in self.gifs_path.glob("*.gif")] # <-- ADICIONE ESTA LINHA

        # --- Timers ---
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.send_proactive_message)

        # Cronômetro para agrupar mensagens rápidas do usuário (debounce)
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.start_ai_response)

        # --- Configuração Inicial ---
        self.setStyleSheet(self.load_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setup_gemini_model()
        
        self.WelcomeWidget = WelcomeWidget
        self.setup_data_and_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LouApp()
    window.show()
    sys.exit(app.exec())