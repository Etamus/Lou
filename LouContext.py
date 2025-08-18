import time
import random
import json
import google.generativeai as genai
from PySide6.QtCore import Signal
from LouIABE import BaseWorker

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
            
            updater_model = genai.GenerativeModel('gemini-2.0-flash')
            
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