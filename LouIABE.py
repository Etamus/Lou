# LouIABE.py
import time
import random
import json
import re
import ast
import google.generativeai as genai
from PySide6.QtCore import QThread, Signal

# --- WORKERS DA IA ---
class BaseWorker(QThread):
    def __init__(self): super().__init__(); self.is_running = True
    def stop(self): self.is_running = False
    def wait_for_finish(self):
        self.stop()
        if self.isRunning(): self.wait()

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
                time.sleep(0.04 + random.uniform(0.0, 0.05))
                self.chunk_ready.emit(chunk.text)
                full_response_text += chunk.text
            if self.is_running: self.stream_finished.emit(full_response_text)
        except Exception as e:
            if self.is_running: self.error_occurred.emit(f"Erro na API: {e}")