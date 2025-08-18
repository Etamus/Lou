# Lou: Framework de Persona Digital Hiper-Realista

Lou é uma plataforma avançada para a criação e interação com personas digitais de alta fidelidade.  
Projetada com uma arquitetura modular e um motor de IA de múltiplas camadas, ela transcende os chatbots tradicionais ao simular uma personalidade coesa, memória contínua e uma consciência situacional sofisticada.

---

## Capacidades Chave da IA e Inovações

### 1. Arquitetura de IA de Duas Etapas: O "Criador" e o "Editor"
Para garantir respostas que são ao mesmo tempo criativas e perfeitamente formatadas, Lou utiliza uma pipeline de IA de duas etapas, separando o processo criativo do técnico:

**IA Criativa (A "Atriz")**: A primeira camada, alimentada pela ficha de personagem completa, tem uma única tarefa: gerar o conteúdo da resposta de forma autêntica e alinhada à personalidade, sem se preocupar com as restrições de formato do chat.

**IA de Formatação (O "Editor")**: Uma segunda IA especialista recebe o texto bruto da "Atriz". Sua única função é analisar a estrutura gramatical e o fluxo natural da resposta e dividi-la em múltiplos balões de chat curtos e cadenciados, garantindo uma experiência de diálogo perfeitamente natural e à prova de falhas.

Esta arquitetura elimina a inconsistência dos modelos de linguagem, permitindo que a criatividade flua sem comprometer a robustez da formatação final.

---

### 2. Motor de Personalidade Externalizado e "Hot-Swap"
O "cérebro" da Lou não está fixo no código. Toda a sua identidade — desde traços psicológicos complexos, histórico de vida, medos e valores, até manias e estilo de comunicação — é definida em um único e detalhado arquivo `personality_prompt.json`.

**Customização Profunda**: Permite a criação de personas radicalmente diferentes e o ajuste fino de seu comportamento em tempo real.

**Recarregamento Dinâmico**: Uma interface de edição integrada permite modificar a personalidade e recarregar o modelo da IA em tempo real, sem a necessidade de reiniciar a aplicação, ideal para testes A/B e desenvolvimento iterativo de personagens.

---

### 3. Consciência Contextual Avançada
Lou demonstra uma compreensão do contexto que vai além do histórico de chat, simulando uma percepção do mundo real.

**Consciência Temporal Contínua**: A IA sabe a data e a hora exatas a cada interação. Isso permite que ela comente sobre o período do dia ("boa noite"), reaja a inconsistências temporais ("Ué, 'boa noite' às duas da tarde?"), e entenda o contexto de feriados ou eventos sazonais.

**Percepção de Latência**: O sistema mede o tempo entre a última mensagem dela e a resposta do usuário. Se um longo período se passa (ex: 3 horas), a IA é instruída a notar a ausência e comentar sobre a demora de forma natural.

---

### 4. Sistema de Memória de Dupla Camada
Para garantir consistência e evolução, a memória da Lou é dividida em duas categorias distintas, que são amostradas e injetadas no contexto a cada interação:

**Memória de Longo Prazo (Backstory)**: Um banco de memórias curado e editável manualmente que constitui a "história de vida" e os fatos imutáveis da personagem.

**Memória de Curto Prazo (Diário de Bordo)**: Após cada conversa, um worker de análise assíncrono cria resumos inteligentes da interação, focando em eventos, decisões e emoções. Isso cria um diário dinâmico que informa a IA sobre o que aconteceu recentemente.

---

### 5. Interação Natural e Proativa
A Lou foi projetada para quebrar o ciclo passivo de "pergunta e resposta".

**Motor de Turno de Conversa (Debouncing)**: A IA compreende o fluxo de uma rajada de mensagens. Ela aguarda inteligentemente o usuário concluir um pensamento antes de formular uma resposta única e coesa, criando um diálogo verdadeiramente natural.

**Engajamento Proativo com Autocorreção**: Se o usuário fica inativo, a Lou tenta reengajar a conversa de forma contextual. O sistema possui um validador de código que inspeciona a tentativa proativa da IA. Se a IA gerar uma frase incompleta (um "mau hábito" comum), o sistema a instrui a se autocorrigir e tentar uma nova abordagem, garantindo que a iniciativa seja sempre de alta qualidade.

**Adaptação de Estilo**: Um worker de análise extrai continuamente padrões de escrita e gírias do usuário, permitindo que a Lou sutilmente adapte seu próprio vocabulário para aumentar o rapport.

---

## Interface e Estrutura Técnica

**Interface Moderna**: Construída com PySide6, a interface é inspirada em aplicativos de chat modernos, incluindo gerenciamento de servidores/canais, avatares customizáveis, sistema de resposta a mensagens e exibição de GIFs animados.

**Arquitetura Modular**: O projeto é segmentado em módulos com responsabilidades claras (`LouFE.py` para UI, `LouBE.py` para lógica, `LouIAFE.py` para integração da IA, etc.), facilitando a manutenção e a escalabilidade.

**Processamento Assíncrono**: Todas as chamadas para a API Gemini são feitas em QThreads, garantindo que a interface permaneça 100% responsiva, mesmo durante o processamento de respostas ou a análise de contexto em segundo plano.

---

## ⚙️ Como Executar

### Pré-requisitos
- Python **3.10+**  
- Chave de API **Google Gemini**  

### Instalação
```bash
# Instale as dependências
pip install PySide6 google-generativeai
```

### Configuração
```bash
    - Acesse as pastas `assets/avatars` e `assets/gifs` e adicione seus avatares e GIFs.
    - Insira sua chave da API da Gemini no arquivo `LouIAFE.py` na variável `API_KEY`.
```

### Execução
```bash
    python LouMain.py
```
