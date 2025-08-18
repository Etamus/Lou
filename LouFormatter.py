import re

def sanitize_and_split_response(text: str) -> list:
        """
        O 'Editor Gramatical Híbrido e Definitivo'. Limpa e divide a resposta da IA
        usando uma hierarquia de regras: GIFs, quebras de linha e análise gramatical.
        """
        # Etapa 0: Lida com GIFs como um caso especial e isolado
        if "GIF:" in text:
            parts = re.split(r'(GIF:\w+)', text)
            return [p.strip() for p in parts if p and p.strip()]

        # Etapa 1: Limpeza Inicial Global
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001FAFF"  # Various Symbols
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text).strip()
        text = text.replace('!', '')
        if text.endswith('.') and not text.endswith('...'):
            text = text[:-1]

        # Etapa 2: Divisão por Quebras de Linha (Regra de Prioridade Alta)
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Etapa 3: Divisão Gramatical de cada linha que ainda for longa
        intermediate_chunks = []
        for line in lines:
            # A regex divide após pontuação forte OU antes de uma letra maiúscula
            # que é precedida por uma letra minúscula ou vírgula.
            sub_chunks = re.split(r'(?<=[.?!…])\s+|(?<=[a-z,])\s+(?=[A-Z])', line)
            intermediate_chunks.extend(sub_chunks)

        # Etapa 4: Limpeza e Capitalização Final
        final_chunks = []
        for i, chunk in enumerate(intermediate_chunks):
            clean_chunk = chunk.strip().rstrip('.,')
            if not clean_chunk:
                continue
            
            # Garante que novas frases (a partir da segunda na sequência geral) comecem com letra maiúscula
            if len(final_chunks) > 0 and clean_chunk and clean_chunk[0].islower():
                final_chunks.append(clean_chunk[0].upper() + clean_chunk[1:])
            else:
                final_chunks.append(clean_chunk)

        return final_chunks