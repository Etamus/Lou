# LouFlixWorker.py
from PySide6.QtCore import Signal
from LouIABE import BaseWorker

class LouFlixWorker(BaseWorker):
    chunk_ready = Signal(str)
    stream_finished = Signal(str)
    error_occurred = Signal(str)

    # Adicionamos is_seek_reaction e seek_details
    def __init__(self, model, history, is_movie_comment, movie_prompt=None, last_movie_context=None, is_seek_reaction=False, seek_details=""):
        super().__init__()
        self.model = model
        self.history = history
        self.is_movie_comment = is_movie_comment
        self.movie_prompt = movie_prompt
        self.last_movie_context = last_movie_context
        # LÓGICA DE SEEK: Novos atributos
        self.is_seek_reaction = is_seek_reaction
        self.seek_details = seek_details

    def run(self):
        if not self.model:
            self.error_occurred.emit("Modelo Gemini não configurado.")
            return

        instruction_prompt = ""
        # LÓGICA DE SEEK: Nova condição para reagir ao pulo no tempo
        if self.is_seek_reaction:
            instruction_prompt = f"""
            [INSTRUÇÃO ESPECIAL: MODO CINEMA - REAÇÃO A PULO NO VÍDEO]
            Você e seu pai estavam assistindo a um filme e ele acabou de pular o vídeo. {self.seek_details}.
            Faça um comentário muito curto e natural sobre esta ação. NÃO comente sobre a cena do filme em si.
            Exemplos: "Opa, pulou uma parte?", "Essa cena de novo!", "Ansioso pra chegar no final, pai? kkkk", "Voltando pra rever o detalhe, né?".
            """
        elif self.is_movie_comment:
            instruction_prompt = f"""
            [INSTRUÇÃO ESPECIAL: MODO CINEMA - GATILHO]
            Você e seu pai estão assistindo a um filme. A cena a seguir acabou de acontecer: "{self.movie_prompt}"
            Faça um comentário curto e natural sobre esta cena, como se estivesse reagindo em tempo real.
            """
        elif self.last_movie_context:
            instruction_prompt = f"""
            [INSTRUÇÃO ESPECIAL: MODO CINEMA - RESPOSTA CONTEXTUAL]
            Você está assistindo a um filme com seu pai. A última cena que você comentou foi: "{self.last_movie_context}".
            Seu pai agora está respondendo diretamente ao seu comentário. Continue essa conversa específica sobre a cena.
            """
        else:
             instruction_prompt = """
            [INSTRUÇÃO ESPECIAL: MODO CINEMA - RESPOSTA GERAL]
            Você está assistindo a um filme com seu pai, mas ele fez um comentário ou pergunta não relacionado à última cena.
            Responda a ele normalmente, mas mantenha o tom de que vocês estão no meio de um filme (seja um pouco breve).
            """

        final_history = self.history + [{"role": "user", "parts": [instruction_prompt]}]
        
        # O resto do método run() permanece o mesmo
        try:
            response = self.model.generate_content(final_history, stream=True)
            full_response_text = ""
            for chunk in response:
                if not self.is_running: response.close(); break
                self.chunk_ready.emit(chunk.text)
                full_response_text += chunk.text
            if self.is_running: self.stream_finished.emit(full_response_text)
        except Exception as e:
            if self.is_running: self.error_occurred.emit(f"Erro na API: {e}")