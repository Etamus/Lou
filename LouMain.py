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

        # Define o caminho para a pasta de dados e a cria se não existir
        self.data_path = Path("data")
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_path / "chat_data.json"
        self.memory_file = self.data_path / "memory_bank.json"

        self.data = {}
        self.long_term_memory = []
        self.server_buttons = {}
        self.channel_buttons = {}
        self.current_server_id = None
        self.current_channel_id = None

        # --- Variáveis de Estado da IA ---
        self.gemini_model = None
        self.worker = None
        self.memory_worker = None
        self.proactive_worker = None
        self.current_ai_message_widget = None
        self.current_ai_raw_text = ""
        self.proactive_attempts = 0

        # --- Timers ---
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.send_proactive_message)

        # --- Configuração Inicial ---
        # A UIMixin fornece o método load_stylesheet
        self.setStyleSheet(self.load_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # A AIFeaturesMixin fornece o método setup_gemini_model
        self.setup_gemini_model()
        
        # A AppLogicMixin fornece o método setup_data_and_ui,
        # que por sua vez usa os métodos da UIMixin para construir a interface.
        self.WelcomeWidget = WelcomeWidget # Passa a classe para o Mixin
        self.setup_data_and_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Garante que as fontes customizadas sejam carregadas se necessário
    # from PySide6.QtGui import QFontDatabase
    # QFontDatabase.addApplicationFont("path/to/font.ttf")
    window = LouApp()
    window.show()
    sys.exit(app.exec())