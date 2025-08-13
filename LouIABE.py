# LouIABE.py
import time
import random
import json
import google.generativeai as genai
from PySide6.QtCore import QThread, Signal

# --- WORKERS DA IA ---
class BaseWorker(QThread):
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
                time.sleep(0.04 + random.uniform(0.0, 0.05))
                self.chunk_ready.emit(chunk.text)
                full_response_text += chunk.text
            
            if self.is_running:
                self.stream_finished.emit(full_response_text)
        except Exception as e:
            if self.is_running:
                self.error_occurred.emit(f"Erro na API: {e}")

# Em LouIABE.py, substitua a classe ContextUpdateWorker

class ContextUpdateWorker(BaseWorker):
    """
    Worker unificado que analisa a conversa para extrair memórias (fatos)
    e padrões de estilo que sejam genuinamente novos, evitando duplicatas.
    """
    context_updated = Signal(dict)

    def __init__(self, conversation_snippet, current_memories, current_styles):
        super().__init__()
        self.snippet = conversation_snippet
        self.current_memories = current_memories
        self.current_styles = current_styles

    def run(self):
        try:
            time.sleep(random.uniform(1, 2))
            
            updater_model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Converte as listas atuais para uma string JSON para incluir no prompt
            memories_str = json.dumps(self.current_memories, ensure_ascii=False)
            styles_str = json.dumps(self.current_styles, ensure_ascii=False)

            prompt = f"""
            Sua tarefa é analisar a conversa abaixo e extrair informações que são NOVAS e RELEVANTES.

            INFORMAÇÕES JÁ SALVAS (NÃO REPITA NEM REFORMULE):
            - Memórias Atuais: {memories_str}
            - Estilos Atuais: {styles_str}

            CONVERSA RECENTE PARA ANÁLISE:
            {self.snippet}

            INSTRUÇÕES:
            1.  Analise a 'CONVERSA RECENTE'.
            2.  Extraia fatos (memories) e padrões de escrita do usuário (styles) que sejam **GENUINAMENTE NOVOS**.
            3.  **NÃO extraia informações que já existem nas listas 'INFORMAÇÕES JÁ SALVAS' ou que são apenas uma pequena variação delas.** (Ex: Se já existe "gosta de rock", não adicione "curte bandas de rock").
            4.  Sua resposta DEVE ser um único objeto JSON com as chaves "memories" e "styles", contendo APENAS as informações novas.

            RESULTADO JSON:
            """
            
            response = updater_model.generate_content(prompt)
            raw_text = response.text

            start_index = raw_text.find('{')
            end_index = raw_text.rfind('}')
            if start_index != -1 and end_index != -1 and start_index < end_index:
                json_str = raw_text[start_index : end_index + 1]
                data = json.loads(json_str)
                context_data = {
                    "memories": data.get("memories", []),
                    "styles": data.get("styles", [])
                }
                self.context_updated.emit(context_data)
                if context_data["memories"] or context_data["styles"]:
                     print(f"--- Novo Contexto Adicionado: {context_data} ---")
            else:
                self.context_updated.emit({})

        except (Exception, json.JSONDecodeError) as e:
            print(f"### ERRO no ContextUpdateWorker: {e} ###")
            self.context_updated.emit({})

# Substitua a classe ProactiveMessageWorker em LouIABE.py

class ProactiveMessageWorker(BaseWorker):
    """
    Worker para gerar mensagens proativas com noção de contexto, emoção e
    limite de tentativas.
    """
    message_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model, history, attempt_count):
        super().__init__()
        self.model = model
        self.history = history
        self.attempt_count = attempt_count

    def run(self):
        if not self.model:
            return
        
        # O prompt muda com base na tentativa
        if self.attempt_count < 2:
            # Primeira tentativa: continuar o assunto ou iniciar um novo de forma contextual
            prompt = """
            O usuário está quieto há um tempo. Gere uma mensagem proativa curta e natural para reengajar a conversa.
            INSTRUÇÕES:
            1.  **Analise o histórico recente:** Qual era o tom da conversa (feliz, sério, curioso)? Mantenha esse tom.
            2.  **Seja relevante:** Você pode continuar o último assunto com uma nova pergunta ou um pensamento relacionado.
            3.  **Ou seja criativa:** Se o assunto anterior terminou, inicie um novo que faça sentido com base no que você sabe sobre seu pai.
            
            **REGRA IMPORTANTE:** Sua mensagem deve ser uma ideia completa. NÃO termine com uma frase que exija que o usuário pergunte 'o quê?', como 'Pai, tava pensando aqui...'. Inicie E complete o pensamento.
            """
        else:
            # Última tentativa: verificar a presença do usuário
            prompt = """
            O usuário está quieto há bastante tempo e não respondeu sua última tentativa de iniciar uma conversa.
            Sua tarefa é enviar uma última mensagem, muito curta e natural, perguntando se ele ainda está aí.
            NÃO puxe outro assunto. Apenas verifique a presença dele.
            Exemplos: "Pai?", "Ta aí?", "Tudo bem por aí, pai?"
            """

        try:
            proactive_history = self.history + [{"role": "user", "parts": [prompt]}]
            response = self.model.generate_content(proactive_history)
            if self.is_running:
                self.message_ready.emit(response.text)
        except Exception as e:
            if self.is_running:
                self.error_occurred.emit(f"Erro ao gerar mensagem proativa: {e}")