import re
import random
import google.generativeai as genai
from PySide6.QtCore import Signal
from LouIABE import BaseWorker

class ProactiveMessageWorker(BaseWorker):
    message_ready = Signal(str); error_occurred = Signal(str)
    def __init__(self, model, history, attempt_count):
        super().__init__(); self.model = model; self.history = history; self.attempt_count = attempt_count
    def run(self):
        if not self.model: return
        if self.attempt_count < 2:
            prompt = """
            CONTEXTO ATUAL: O usuário ('Pai') está em silêncio. A última mensagem na conversa foi sua (de Lou). Sua tarefa é quebrar o silêncio com um novo pensamento ou pergunta. NÃO é para responder à sua própria última mensagem.

            DIRETRIZES TÉCNICAS (OBRIGATÓRIAS):
            1.  Sua resposta DEVE ser um pensamento completo e autônomo.
            2.  É ESTRITAMENTE PROIBIDO gerar frases que dependam de uma resposta do usuário para serem completadas (Ex: "Pai, pensando aqui...").
            3.  Você deve INICIAR e CONCLUIR a ideia na sua mensagem.

            DIRETRIZES DE CONTEÚDO (COMO PENSAR):
            1.  **Analise o histórico recente:** Qual era o tom da conversa (feliz, sério, curioso)? Mantenha esse tom.
            2.  **Seja relevante:** Você pode continuar o último assunto com uma nova pergunta ou um pensamento relacionado (mas não como uma resposta direta à sua última fala).
            3.  **Ou seja criativa:** Se o assunto anterior terminou, inicie um novo que faça sentido com base no que você sabe sobre seu pai.
            """
        else:
            prompt = """
            O usuário está quieto há bastante tempo e não respondeu sua última tentativa.
            Sua tarefa é enviar uma última mensagem, muito curta e natural, perguntando se ele ainda está aí.
            NÃO puxe outro assunto. Apenas verifique a presença dele. Exemplos: "Pai?", "Ta aí?", "Tudo bem por aí?"
            """
        try:
            proactive_history = self.history + [{"role": "user", "parts": [prompt]}]
            response = self.model.generate_content(proactive_history)
            
            # Validador de Resposta (mantido da correção anterior)
            generated_text = response.text.strip()
            forbidden_patterns = re.compile(r'.*(pensando aqui|lembrei de|sabe o que)\.*$', re.IGNORECASE)
            final_text = generated_text
            if self.attempt_count < 2 and forbidden_patterns.match(generated_text):
                print(f"--- AVISO: IA gerou uma mensagem proativa incompleta ('{generated_text}'). Solicitando autocorreção. ---")
                corrective_prompt = f"""
                Sua última tentativa de mensagem proativa foi um pensamento incompleto e proibido. A mensagem foi: '{generated_text}'.
                Isto está errado porque depende que o usuário pergunte 'o quê?'.
                Por favor, gere uma NOVA e DIFERENTE mensagem proativa que seja um pensamento COMPLETO.
                Inicie e conclua a ideia.
                """
                corrective_history = self.history + [{"role": "user", "parts": [corrective_prompt]}]
                new_response = self.model.generate_content(corrective_history)
                corrected_text = new_response.text.strip()
                if forbidden_patterns.match(corrected_text):
                    final_text = "E aí, pai, tudo quieto por aí?"
                else:
                    final_text = corrected_text
            
            if self.is_running:
                self.message_ready.emit(final_text)

        except Exception as e:
            if self.is_running: self.error_occurred.emit(f"Erro ao gerar mensagem proativa: {e}")