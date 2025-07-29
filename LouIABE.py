import time
import random
import json
import google.generativeai as genai
from PySide6.QtCore import QThread, Signal

# --- WORKERS DA IA ---
class BaseWorker(QThread):
    """Worker base para garantir que a thread possa ser parada de forma segura."""
    def __init__(self):
        super().__init__()
        self.is_running = True

    def stop(self):
        self.is_running = False

    def wait_for_finish(self):
        self.stop()
        if self.isRunning():
            self.wait()

class GeminiWorker(BaseWorker):
    """Worker para gerar respostas do chat principal em modo streaming."""
    chunk_ready = Signal(str)
    stream_finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model, history_with_context):
        super().__init__()
        self.model = model
        self.history = history_with_context

    def run(self):
        if not self.model:
            self.error_occurred.emit("Modelo Gemini não configurado.")
            return
        try:
            response = self.model.generate_content(self.history, stream=True)
            full_response_text = ""
            for chunk in response:
                if not self.is_running:
                    response.close()
                    break
                # Simula um delay de digitação mais natural
                time.sleep(0.04 + random.uniform(0.0, 0.05))
                self.chunk_ready.emit(chunk.text)
                full_response_text += chunk.text
            
            if self.is_running:
                self.stream_finished.emit(full_response_text)
        except Exception as e:
            if self.is_running:
                self.error_occurred.emit(f"Erro na API: {e}")

class MemoryExtractorWorker(BaseWorker):
    """Worker para extrair memórias de longo prazo de um trecho da conversa."""
    memories_extracted = Signal(list)

    def __init__(self, conversation_snippet):
        super().__init__()
        self.snippet = conversation_snippet

    def run(self):
        try:
            extractor_model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""Analise o seguinte trecho de conversa. Extraia apenas fatos importantes e de longo prazo em uma lista JSON. Se não houver nenhum, retorne []. Conversa: {self.snippet} Resultado:"""
            response = extractor_model.generate_content(prompt)
            # Limpa a resposta para garantir que seja um JSON válido
            clean_response = response.text.strip().replace("```json", "").replace("```", "")
            memories = json.loads(clean_response)
            if isinstance(memories, list):
                self.memories_extracted.emit(memories)
        except (Exception, json.JSONDecodeError):
            self.memories_extracted.emit([]) # Emite lista vazia em caso de erro

class ProactiveMessageWorker(BaseWorker):
    """Worker para gerar mensagens proativas quando o usuário está inativo."""
    message_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model, history):
        super().__init__()
        self.model = model
        self.history = history

    def run(self):
        if not self.model:
            return
        try:
            prompt = """O usuário está quieto há um tempo. Puxe assunto de forma natural e curta. Olhe o histórico e o contexto da memória. Pode ser uma pergunta aleatória, um pensamento seu, ou algo que você lembrou."""
            proactive_history = self.history + [{"role": "user", "parts": [prompt]}]
            response = self.model.generate_content(proactive_history)
            if self.is_running:
                self.message_ready.emit(response.text)
        except Exception as e:
            if self.is_running:
                self.error_occurred.emit(f"Erro ao gerar mensagem proativa: {e}")