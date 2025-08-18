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

class ContextUpdateWorker(BaseWorker):
    """
    Worker unificado que:
    1. Cria resumos da conversa para a memória de curto prazo.
    2. Analisa APENAS o estilo de fala do usuário.
    """
    context_updated = Signal(dict)

    def __init__(self, conversation_snippet, current_short_term_memories, current_styles):
        super().__init__()
        self.snippet = conversation_snippet
        self.current_memories = current_short_term_memories
        self.current_styles = current_styles

    def run(self):
        try:
            time.sleep(random.uniform(1, 2))
            
            updater_model = genai.GenerativeModel('gemini-1.5-flash')
            
            memories_str = json.dumps(self.current_memories, ensure_ascii=False)
            styles_str = json.dumps(self.current_styles, ensure_ascii=False)

            prompt = f"""
            Sua tarefa é analisar a conversa entre 'Mateus' (o usuário) e 'Lou' (a IA) e extrair dois tipos de informação nova e relevante.

            INFORMAÇÕES JÁ SALVAS (NÃO REPITA NEM REFORMULE):
            - Resumos Anteriores (memories): {memories_str}
            - Estilos de Mateus (styles): {styles_str}

            CONVERSA RECENTE PARA ANÁLISE:
            {self.snippet}

            INSTRUÇÕES:
            1.  **Memories (Resumo):** Crie um ou dois resumos muito curtos (5-10 palavras cada) dos pontos principais da conversa recente. Foco em eventos, decisões ou sentimentos expressos.
            2.  **Styles (Estilo do Usuário):** Analise APENAS as falas de 'Mateus'. Extraia padrões de escrita, gírias ou abreviações que ELE usou e que ainda não estão na lista de estilos. NÃO analise a fala da 'Lou'.
            3.  **NÃO extraia informações que já existem nas listas acima ou que são variações óbvias.**
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