# ✨ Lou

Inteligência artificial com personalidade customizável, projetada para diálogos naturais, interações contextuais profundas e memória a longo prazo.

---

## Funcionalidades Principais

### Interface de Mensagens
- **Gerenciamento Completo:** Crie, renomeie, exclua e personalize servidores (grupos) e canais de texto com ícones customizáveis.
- **Diálogos Intuitivos:** Todas as janelas de gerenciamento possuem um design limpo, mantendo a consistência visual.
- **Personalização de Perfil:** Altere seu nome de usuário e foto de perfil, com as mudanças sendo refletidas instantaneamente nas novas mensagens e na interface.

### Chat Moderno e Contextual
- **Timestamp e Data:** Cada mensagem exibe a hora de envio, e o histórico é visualmente separado por dia com um marcador de data.
- **Sistema de Resposta:** Responda a mensagens específicas da IA, com um indicador visual que mostra a qual mensagem você está respondendo.
- **Suporte a GIFs:** A IA pode enviar GIFs animados (armazenados localmente em `assets/gifs`) quando achar apropriado para se expressar.
- **Layout Inteligente:** A largura dos balões de chat se ajusta para otimizar a leitura, e o layout de mensagens com GIFs é tratado de forma especial para não quebrar a interface.

---

## Comportamento da Lou

### Personalidade Profunda e Customizável
- **Ficha de Personagem Externa:** A personalidade completa da Lou (identidade, traços, psicologia, medos, hobbies, etc.) é carregada a partir de um único arquivo `personality_prompt.json`, permitindo total customização sem alterar o código.
- **Noção de Tempo e Espaço:** A IA sabe a data e hora atuais, permitindo interações contextuais sobre o período do dia, datas especiais e feriados.
- **Raciocínio Transparente (Debug):** O terminal exibe uma breve explicação do "raciocínio" da IA, mostrando quais traços de personalidade ela usou para formular sua resposta.

### Memória e Aprendizado Contínuo
- **Aprendizado Unificado:** Após cada conversa, um worker (`ContextUpdateWorker`) analisa a interação e extrai simultaneamente:
  - **Memórias Factuais:** Fatos importantes para consistência a longo prazo (`memory_bank.json`).
  - **Padrões de Estilo:** Gírias e formas de falar do usuário para adaptação (`style_bank.json`).
- **Interação Natural:**
  - **Debouncing de Mensagens:** A IA aguarda você terminar de digitar múltiplas mensagens em sequência para respondê-las como um único pensamento, evitando respostas apressadas e erros.
  - **Fala Proativa com Limites:** Se o chat ficar inativo, a Lou tentará reengajar a conversa de forma contextual. Após um número limitado de tentativas sem resposta, ela perguntará pela sua presença e depois aguardará em silêncio.

---

## Estrutura Técnica

### Arquitetura Modular em Python
- **Código Organizado:** O projeto é dividido em módulos com responsabilidades claras (`LouFE.py` para front-end, `LouBE.py` para lógica, `LouIAFE.py` para integração da IA, etc.).
- **Interface com PySide6:** A interface gráfica é construída utilizando o framework moderno Qt for Python.
- **Comunicação Assíncrona com a IA:** Todas as chamadas para a API Gemini são feitas em `QThread`s separadas para garantir que a interface nunca congele, mesmo durante o processamento de respostas ou a análise de contexto.

### Robustez e Tratamento de Erros
- **Parser de Respostas Inteligente:** O sistema é resiliente a variações no formato da resposta da IA. Ele é capaz de processar JSONs perfeitos, JSONs com erros de formatação (como aspas escapadas) e até mesmo texto plano com quebras de linha, sempre extraindo as mensagens corretamente.
- **Gerenciamento de Recursos:** GIFs são carregados e exibidos de forma otimizada para não consumir memória excessiva, e os workers de IA são criados e destruídos de forma segura para evitar `race conditions`.

---

## Como Executar

1.  **Pré-requisitos:**
    - Python 3.10+
    - Uma chave de API da **Google Gemini**.

2.  **Instalação:**
    ```bash
    # Instale as dependências
    pip install PySide6 google-generativeai
    ```

3.  **Configuração:**
    - Crie as pastas `assets/avatars` e `assets/gifs` e adicione seus avatares e GIFs.
    - Crie a pasta `data` e adicione o arquivo `personality_prompt.json` com a estrutura da personalidade da Lou.
    - Insira sua chave da API da Gemini no arquivo `LouIAFE.py` na variável `API_KEY`.

4.  **Execução:**
    ```bash
    python LouMain.py
    ```
