# 💬 Lou - IA de Conversação

IA de conversação com foco em interatividade natural e alto nível de personalização via fine-tuning. Projetada para diálogos fluidos, resposta contextual e integração com memória a longo prazo.

---

## 🧩 Funcionalidades Principais

### 🖼️ Interface Personalizável
- Renomear grupos e canais (texto e voz) diretamente pelo clique direito.
- Alterar nome e foto do usuário com refletência imediata:
  - No rodapé da interface.
  - Em cada nova mensagem enviada.
- Imagem do grupo preenche totalmente o ícone (sem bordas quadradas).
- Layout dos grupos centralizado na lateral esquerda (não colado na borda).

### 🗣️ Chat de Voz Estilo Discord
- Entrar e sair de chats de voz sem trocar o canal de texto.
- Avatar e nome aparecem abaixo do chat de voz.
- Entradas automáticas (ex: Lou entra segundos depois do usuário).
- Ícones de microfone mutado visíveis.
- IA permanece escutando e pode responder proativamente.

### 💬 Chat de Texto Moderno
- Mensagens com avatar e nome acima (usuário e Lou).
- Transições suaves entre canais (sem bug visual).
- Indicação de digitação com texto "Digitando..." no lugar de "...".
- Clique com botão direito em canais ou grupos para:
  - Excluir (botão vermelho).
  - Renomear (edição inline).

---

## 🤖 Comportamento da IA (Lou)

### 🎭 Personalidade e Estilo
- Lou sabe o nome do usuário.
- Usa humor inteligente e respostas sarcásticas.
- Fala mais devagar e com pausas naturais.
- Fala proativa com base em contexto e tempo de silêncio.
- IA entra em “modo conversa ativa” após interações.

### 🧠 Memória
- Memória factual: fatos extraídos de conversas anteriores.
- Memória de estilo: gírias, padrões e expressões comuns do usuário são aprendidos dinamicamente.
- Memória persistente salva em arquivos `.json`:
  - `memory_bank.json` → fatos.
  - `style_bank.json` → estilo.

---

## ⚒️ Estrutura Técnica

### 🧵 Execução Assíncrona
- Threads separadas para:
  - Reconhecimento de voz.
  - Consulta à IA.
  - Fala (TTS).
- Uso de `Queue` para sincronização entre eventos.
- Sistema robusto contra deadlocks e travamentos.

### ❗ Tratamento de Erros
- Textos vazios ou falta de resposta da IA foram resolvidos:
  - Garantia de resposta com fallback.
  - Log detalhado e modo seguro de fallback.
- Crashes ao trocar de canais corrigidos com transições visuais suaves.
- Erros de áudio e threads congeladas tratados com verificação e reinício seguro.

---

## 🔐 Requisitos

- Python 3.10+
  - API da Gemini (Google)
- Assets (imagens de usuário e grupos)
