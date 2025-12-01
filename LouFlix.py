# LouFlix.py
import json
import random
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QFrame, QScrollArea, QWidget, QSplitter, QSlider)
from PySide6.QtCore import QTimer, QTime, Qt, QUrl
from PySide6.QtGui import QScreen
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from LouFE import ChatInput, ChatMessageWidget
from LouIAFE import AIFeaturesMixin
from LouFlixWorker import LouFlixWorker
from LouFormatter import sanitize_and_split_response

class MoviePlayerWindow(QDialog, AIFeaturesMixin):
    def __init__(self, main_app_instance, parent=None):
        super().__init__(parent)
        # ... (O __init__ continua igual até a parte dos timers) ...
        self.main_app = main_app_instance
        self.setWindowTitle("Modo Cinema")
        self.setMinimumSize(1280, 720); self.resize(1600, 720)
        base_style = self.main_app.load_stylesheet()
        minimalist_style = """
            QFrame#controlBar { background-color: #202225; border-top: 1px solid #36393f; }
            QPushButton#minimalistControlButton { background-color: transparent; color: #96989d; border: none; font-size: 16pt; padding: 6px; border-radius: 5px; }
            QPushButton#minimalistControlButton:hover { background-color: #2f3136; color: #ffffff; }
            QPushButton#minimalistControlButton:checked { color: #ffffff; }
            QLabel#movieTimeLabel { color: #96989d; font-weight: bold; font-size: 10pt; }
            QSlider::groove:horizontal { background: #40444b; height: 6px; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #5865f2; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background-color: #ffffff; border: none; height: 16px; width: 16px; margin: -5px 0; border-radius: 8px; }
        """
        self.setStyleSheet(base_style + minimalist_style)
        self.triggers = []; self.current_trigger_index = 0; self.chat_history = []
        self.last_movie_context = None
        self.timer = QTimer(self); self.timer.setInterval(100)
        self.timer.timeout.connect(self._on_timer_tick);
        self.response_delay_timer = QTimer(self); self.response_delay_timer.setSingleShot(True)
        self.response_delay_timer.timeout.connect(self.start_ai_response)
        self._pending_ai_request = {}
        self.player = QMediaPlayer(); self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output); self.audio_output.setVolume(1.0)
        self.video_widget = QVideoWidget(); self.player.setVideoOutput(self.video_widget)
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_widget.setAspectRatioMode(Qt.KeepAspectRatio)
        self.player.positionChanged.connect(self._update_slider_position)
        self.player.durationChanged.connect(self._set_slider_range)
        self.gemini_model = self.main_app.gemini_model; self.data = self.main_app.data
        self.worker = None; self.current_ai_message_widget = None; self.current_ai_raw_text = ""
        
        # LÓGICA DE SEEK: Estado de cooldown para evitar spam de comentários
        self.seek_cooldown_active = False

        self._setup_ui()

    # LÓGICA DE SEEK: Novo método para lidar com o pulo no tempo
    def _handle_seek(self, old_position, new_position):
        if self.seek_cooldown_active or abs(old_position - new_position) < 3000: # Ignora pequenos ajustes
            return
            
        # 1. Ativa o cooldown para pausar gatilhos de tempo
        self.seek_cooldown_active = True
        QTimer.singleShot(7000, lambda: setattr(self, 'seek_cooldown_active', False)) # Cooldown de 7s

        # 2. Gera a reação da IA
        old_time_str = QTime.fromMSecsSinceStartOfDay(old_position).toString("mm:ss")
        new_time_str = QTime.fromMSecsSinceStartOfDay(new_position).toString("mm:ss")
        seek_dir = "pulou para frente" if new_position > old_position else "voltou"
        details = f"Ele {seek_dir} no vídeo de {old_time_str} para {new_time_str}"
        self._request_ai_response(is_seek_reaction=True, seek_details=details)

        # 3. Ressincroniza os gatilhos
        new_time_full_str = QTime.fromMSecsSinceStartOfDay(new_position).toString("HH:mm:ss")
        for trigger in self.triggers:
            if trigger['timestamp'] < new_time_full_str:
                trigger['triggered'] = True
            else:
                trigger['triggered'] = False
        
        self.current_trigger_index = next((i for i, t in enumerate(self.triggers) if not t.get('triggered')), len(self.triggers))

    def _set_player_position(self, position):
        old_pos = self.player.position()
        self.player.setPosition(position)
        self._handle_seek(old_pos, position) # Chama o handler de seek

    # ... (O resto do código até _on_timer_tick permanece o mesmo)
    def _center_on_screen(self):
        screen_geometry = self.screen().geometry()
        self_geometry = self.frameGeometry()
        self_geometry.moveCenter(screen_geometry.center())
        self.move(self_geometry.topLeft())
    def showEvent(self, event):
        self._center_on_screen(); super().showEvent(event)
    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        video_panel_widget = QWidget()
        video_panel_layout = QVBoxLayout(video_panel_widget)
        video_panel_layout.setContentsMargins(0, 0, 0, 0); video_panel_layout.setSpacing(0)
        video_panel_layout.addWidget(self.video_widget, 1)
        control_bar_frame = QFrame()
        control_bar_frame.setObjectName("controlBar")
        control_bar_frame.setFixedHeight(60)
        control_bar_layout = QHBoxLayout(control_bar_frame)
        control_bar_layout.setContentsMargins(15, 0, 15, 0)
        self.play_pause_button = QPushButton("▶"); self.play_pause_button.setToolTip("Reproduzir")
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("movieTimeLabel")
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.sliderMoved.connect(self._set_player_position) # O slider agora chama o _set_player_position
        self.load_button = QPushButton("📁"); self.load_button.setToolTip("Carregar Sessão")
        self.play_pause_button.setObjectName("minimalistControlButton")
        self.load_button.setObjectName("minimalistControlButton")
        self.play_pause_button.setCheckable(True)
        self.play_pause_button.clicked.connect(self._toggle_playback)
        self.play_pause_button.setEnabled(False)
        self.load_button.clicked.connect(self._load_session)
        control_bar_layout.addWidget(self.play_pause_button)
        control_bar_layout.addWidget(self.time_label)
        control_bar_layout.addWidget(self.progress_slider, 1)
        control_bar_layout.addWidget(self.load_button)
        video_panel_layout.addWidget(control_bar_frame)
        splitter.addWidget(video_panel_widget)
        chat_panel_widget = QWidget()
        chat_panel_layout = QVBoxLayout(chat_panel_widget)
        chat_panel_layout.setContentsMargins(0, 0, 0, 0); chat_panel_layout.setSpacing(0)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True); self.scroll_area.setObjectName("chat_scroll_area")
        self.chat_container = QWidget(); self.chat_layout = QVBoxLayout(self.chat_container); self.chat_layout.addStretch()
        self.scroll_area.setWidget(self.chat_container); self.chat_layout.setContentsMargins(10, 10, 10, 20)
        input_frame = QFrame(); input_frame.setObjectName("chat_input_frame")
        input_layout = QHBoxLayout(input_frame)
        self.text_input = ChatInput(); self.text_input.sendMessage.connect(self._on_user_message)
        input_layout.addWidget(self.text_input)
        input_area = QWidget(); input_area_layout = QVBoxLayout(input_area)
        input_area_layout.setContentsMargins(15, 10, 15, 20); input_area_layout.addWidget(input_frame)
        chat_panel_layout.addWidget(self.scroll_area, 1)
        chat_panel_layout.addWidget(input_area)
        splitter.addWidget(chat_panel_widget)
        splitter.setSizes([1000, 600])
        self.main_layout.addWidget(splitter)
    def _toggle_playback(self, checked):
        if checked:
            self.player.play(); self.timer.start()
            self.play_pause_button.setText("II"); self.play_pause_button.setToolTip("Pausar")
        else:
            self.player.pause(); self.timer.stop()
            self.play_pause_button.setText("▶"); self.play_pause_button.setToolTip("Reproduzir")
    def _update_slider_position(self, position):
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)
        duration = self.player.duration()
        time_format = "mm:ss" if duration < 3600000 else "HH:mm:ss"
        current_time = QTime.fromMSecsSinceStartOfDay(position).toString(time_format)
        total_time = QTime.fromMSecsSinceStartOfDay(duration).toString(time_format)
        self.time_label.setText(f"{current_time} / {total_time}")
    def _set_slider_range(self, duration):
        self.progress_slider.setRange(0, duration)

    def _on_timer_tick(self):
        # LÓGICA DE SEEK: Adicionada verificação de cooldown
        if self.player.playbackState() != QMediaPlayer.PlayingState or self.seek_cooldown_active:
            return
        if self.worker and self.worker.isRunning(): return
        
        if self.current_trigger_index < len(self.triggers):
            media_pos = self.player.position()
            current_time_str = QTime.fromMSecsSinceStartOfDay(media_pos).toString("HH:mm:ss")
            next_trigger = self.triggers[self.current_trigger_index]
            
            if not next_trigger.get('triggered', False) and current_time_str >= next_trigger['timestamp']:
                self._trigger_timed_comment(next_trigger['prompt'])
                next_trigger['triggered'] = True
                self.current_trigger_index = next((i for i, t in enumerate(self.triggers) if not t.get('triggered')), len(self.triggers))
    
    # LÓGICA DE SEEK: _request_ai_response e start_ai_response precisam lidar com o novo tipo de chamada
    def _request_ai_response(self, is_movie_comment=False, movie_prompt=None, is_seek_reaction=False, seek_details=""):
        if self.worker and self.worker.isRunning(): return
        self._pending_ai_request = {
            "is_movie_comment": is_movie_comment, "movie_prompt": movie_prompt,
            "is_seek_reaction": is_seek_reaction, "seek_details": seek_details
        }
        self.response_delay_timer.start(random.randint(800, 2500))

    def start_ai_response(self):
        params = self._pending_ai_request
        history_for_ai = self.chat_history[-10:]
        self.add_message_to_chat({"role": "model", "parts": ["..."]}, is_streaming=True)
        current_context = self.last_movie_context if not params["is_movie_comment"] and not params["is_seek_reaction"] else None
        self.worker = LouFlixWorker(self.gemini_model, history_for_ai, 
                                   params["is_movie_comment"], params["movie_prompt"], 
                                   current_context, params["is_seek_reaction"], params["seek_details"])
        if current_context: self.last_movie_context = None
        self.worker.chunk_ready.connect(self.handle_chunk)
        self.worker.stream_finished.connect(self.handle_stream_finished)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    # ... (O resto dos métodos (_on_user_message, _trigger_timed_comment, etc.) continuam os mesmos)
    def _on_user_message(self, text):
        text_stripped = text.strip()
        if not text_stripped: return
        self.add_message_to_chat({"role": "user", "parts": [text_stripped]})
        self.text_input.clear()
        self._request_ai_response()
    def _trigger_timed_comment(self, prompt_text):
        self.last_movie_context = prompt_text
        self._request_ai_response(is_movie_comment=True, movie_prompt=prompt_text)
    def _load_session(self):
        json_path, _ = QFileDialog.getOpenFileName(self, "1/2: Selecione o arquivo de gatilhos (.json)", "", "JSON Files (*.json)")
        if not json_path: return
        video_path, _ = QFileDialog.getOpenFileName(self, "2/2: Selecione o arquivo de vídeo", "", "Video Files (*.mp4 *.mkv *.avi *.mov)")
        if not video_path: return
        try:
            with open(json_path, "r", encoding="utf-8") as f: self.triggers = json.load(f)
            for trigger in self.triggers: trigger.pop('triggered', None)
            self.triggers.sort(key=lambda x: x['timestamp'])
            self.player.setSource(QUrl.fromLocalFile(video_path))
            self.play_pause_button.setEnabled(True)
            self.current_trigger_index = 0
            while self.chat_layout.count() > 1:
                item = self.chat_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            self.chat_history.clear()
            self._add_system_message_to_chat(f"Sessão '{Path(video_path).stem}' carregada. Pronto para começar.")
        except Exception as e:
            self._add_system_message_to_chat(f"Erro ao carregar os arquivos: {e}")
    def add_message_to_chat(self, message_data, is_loading=False, is_streaming=False, is_grouped=False):
        widget = ChatMessageWidget(message_data, self.data.get("profiles", {}), is_grouped, self, show_reply_button=False)
        if is_streaming: self.current_ai_message_widget = widget
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, widget)
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))
        if not is_streaming:
            if self.chat_history and self.chat_history[-1]["parts"] == ["..."]: self.chat_history[-1] = message_data
            else: self.chat_history.append(message_data)
        elif is_streaming:
             if not (self.chat_history and self.chat_history[-1]["parts"] == ["..."]): self.chat_history.append(message_data)
    def _add_system_message_to_chat(self, text):
        sys_label = QLabel(f"<i>{text}</i>")
        sys_label.setAlignment(Qt.AlignCenter)
        sys_label.setStyleSheet("color: #72767d; padding: 10px;")
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, sys_label)
    def finalize_response(self):
        pass
    def closeEvent(self, event):
        self.player.stop()
        if self.worker and self.worker.isRunning():
            self.worker.wait_for_finish()
        event.accept()