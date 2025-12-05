const API_BASE = "/api";
let profiles = {};

const state = {
  servers: [],
  activeServerId: null,
  activeChannelId: null,
  isLoading: true,
  voiceChannels: [],
};

const elements = {
  serverRail: document.querySelector("[data-role=server-rail]"),
  channelList: document.querySelector("[data-role=channel-list]"),
  voiceChannelList: document.querySelector("[data-role=voice-channel-list]"),
  messageList: document.querySelector("[data-role=message-list]"),
  emptyState: document.querySelector("[data-role=empty-state]"),
  channelCreateButton: document.querySelector("[data-role=create-channel]"),
  userAvatar: document.querySelector("[data-bind=user-avatar]"),
  userName: document.querySelector("[data-bind=user-name]"),
  messageForm: document.getElementById("message-form"),
  messageInput: document.getElementById("message-input"),
  serverSettingsButton: document.querySelector("[data-role=server-settings]"),
  profileSettingsButton: document.querySelector("[data-role=profile-settings]"),
  modalRoot: document.querySelector("[data-role=modal-root]"),
  replyIndicator: document.querySelector("[data-role=reply-indicator]"),
  replyAuthor: document.querySelector("[data-role=reply-author]"),
  replySnippet: document.querySelector("[data-role=reply-snippet]"),
  replyCancel: document.querySelector("[data-role=reply-cancel]"),
  aiAvailability: document.querySelector("[data-role=ai-availability]"),
  aiAvailabilityLabel: document.querySelector("[data-role=ai-availability-label]"),
  personalityButton: document.querySelector("[data-role=personality-editor]"),
  personalityOverlay: document.querySelector("[data-role=personality-overlay]"),
  personalityPanel: document.querySelector("[data-role=personality-panel]"),
  personalityCategoryList: document.querySelector("[data-role=personality-category-list]"),
  personalityFields: document.querySelector("[data-role=personality-fields]"),
  personalityEmpty: document.querySelector("[data-role=personality-empty]"),
  personalityStatus: document.querySelector("[data-role=personality-status]"),
  personalitySave: document.querySelector("[data-role=personality-save]"),
  personalityCancel: document.querySelector("[data-role=personality-cancel]"),
  personalityClose: document.querySelector("[data-role=personality-close]"),
  contextToggle: document.querySelector("[data-role=context-toggle]"),
  contextOverlay: document.querySelector("[data-role=context-overlay]"),
  contextPanel: document.querySelector("[data-role=context-panel]"),
  contextClose: document.querySelector("[data-role=context-close]"),
  contextStatus: document.querySelector("[data-role=context-status]"),
  contextListShort: document.querySelector("[data-role=context-list-short]"),
  contextListLong: document.querySelector("[data-role=context-list-long]"),
  contextListStyle: document.querySelector("[data-role=context-list-style]"),
  proactiveTrigger: document.querySelector("[data-role=proactive-trigger]"),
  availabilityToggle: document.querySelector("[data-role=availability-toggle]"),
  availabilityToggleLabel: document.querySelector("[data-role=availability-toggle-label]"),
  availabilityToggleDot: document.querySelector("[data-role=availability-toggle-dot]"),
  gifButton: document.querySelector("[data-role=gif-button]"),
  gifOverlay: document.querySelector("[data-role=gif-overlay]"),
  gifPanel: document.querySelector("[data-role=gif-panel]"),
  gifClose: document.querySelector("[data-role=gif-close]"),
  gifUpload: document.querySelector("[data-role=gif-upload]"),
  gifStatus: document.querySelector("[data-role=gif-status]"),
  gifList: document.querySelector("[data-role=gif-list]"),
  gifSearch: document.querySelector("[data-role=gif-search]"),
  gifFileInput: document.querySelector("[data-role=gif-file-input]"),
  voiceSession: document.querySelector("[data-role=voice-session]"),
  voiceSessionStatus: document.querySelector("[data-role=voice-session-status]"),
  voiceParticipants: document.querySelector("[data-role=voice-participants]"),
  voiceLeave: document.querySelector("[data-role=voice-leave]"),
  voiceShare: document.querySelector("[data-role=voice-share]"),
  voiceShareTitle: document.querySelector("[data-role=voice-share-title]"),
  voiceShareStatus: document.querySelector("[data-role=voice-share-status]"),
  voiceShareVideo: document.querySelector("[data-role=voice-share-video]"),
  voiceShareStop: document.querySelector("[data-role=voice-share-stop]"),
  voiceShareTrigger: document.querySelector("[data-role=voice-share-trigger]"),
  voiceShareFileInput: document.querySelector("[data-role=voice-share-file]"),
  voiceShareToggle: document.querySelector("[data-role=voice-share-toggle]"),
  voiceShareCollapseBanner: document.querySelector("[data-role=voice-share-collapse-banner]"),
  voicePresenceIndicator: document.querySelector("[data-role=voice-presence-indicator]"),
};

const bindings = {
  serverName: document.querySelectorAll('[data-bind="server-name"]'),
  channelName: document.querySelectorAll('[data-bind="channel-name"]'),
  channelTopic: document.querySelectorAll('[data-bind="channel-topic"]'),
};

const modalState = {
  node: null,
  escHandler: null,
};

const replyState = {
  serverId: null,
  channelId: null,
  message: null,
};

const personalityState = {
  data: null,
  draft: null,
  activeCategory: null,
  isLoading: false,
  isSaving: false,
  hasUnsavedChanges: false,
};

const contextState = {
  snapshot: { long_term: [], short_term: [], styles: [] },
  isLoading: false,
  isOpen: false,
  hasLoaded: false,
};

const voiceState = {
  channels: [],
  activeChannelId: null,
  participants: [],
  aiChannelId: null,
  aiPresenceSource: null,
  share: null,
  isShareMinimized: false,
  aiShareBackgrounded: false,
};

const voiceMediaLibrary = {
  items: [],
  isLoading: false,
  lastLoadedAt: 0,
  promise: null,
};

const voicePlaybackState = {
  unmuteTimerId: null,
  resumeOnInteractHandler: null,
  pendingPlayPromise: null,
  audioContext: null,
  isUnlocked: false,
  readyHandler: null,
  readyErrorHandler: null,
  unlockListenersAttached: false,
};

const voiceIntentState = {
  pending: [],
};

const VOICE_ACTION_DELAY_MS = 3000;
const AI_AUTO_LEAVE_DELAY_MS = 45000;

const voiceTimers = {
  aiAutoLeaveTimeoutId: null,
};

let channelLimitMeasureFrame = null;

const VOICE_JOIN_PATTERNS = [
  /(lou\s*)?(entra|cola|vem|participa|aparece|conecta)\s+(?:pro|pra|para|no|na)\s+(?:chat\s+de\s+)?(?:voz|call|canal)/i,
  /(entra|cola|vem)\s+(?:no|na|pro|pra)\s+(?:chat\s+de\s+)?voz/i,
  /(entra|vai)\s+(?:sozinha|sozinho|primeiro).*(voz|call|canal)/i,
  /(preciso|quero|manda|chama).*(lou|ela).*(voz|call|canal)/i,
];

const VOICE_SHARE_PATTERNS = [
  /(bora|vamos|vamo)\s+(ver|assistir)/i,
  /(coloca|bota|poe|manda|roda|solta|passa).*(video|filme|transmissao|algo)/i,
  /(transmite|transmitir|compartilha|compartilhar|streama|stream|inicia).*(video|filme|tela|transmissao|algo)?/i,
  /(quero|preciso).*(assistir|ver).*(video|filme)/i,
  /(trasmit|trasmite|trasmitir|trasmissao|trasmisao)/i,
];

const VOICE_CHANNEL_TERMS = [
  "voz",
  "call",
  "chamada",
  "chamadao",
  "canal",
  "canal de voz",
  "vc",
  "voice",
  "sala",
  "ligacao",
  "conferencia",
  "audio",
  "cal",
  "chamada de voz",
];

const VOICE_JOIN_VERBS = [
  "entra",
  "chega",
  "cola",
  "vem",
  "participa",
  "aparece",
  "comparece",
  "brota",
  "pull",
  "join",
  "conecta",
  "sobe",
  "desce",
  "encosta",
  "parece",
  "invade",
];

const VOICE_SUMMON_TERMS = ["lou", "louzinha", "assistente", "sua ia", "minha ia", "iai" , "a ia"];

const VOICE_SHARE_VERBS = [
  "transmit",
  "transmi",
  "compartilh",
  "stream",
  "passa",
  "coloca",
  "bota",
  "mostra",
  "apresenta",
  "solta",
  "manda",
  "exibe",
  "projeta",
  "reproduz",
  "roda",
  "abre",
  "liga",
  "starta",
  "inicia",
  "dropa",
  "trasmit",
  "trasmite",
  "trasmiss",
];

const VOICE_MEDIA_TERMS = [
  "video",
  "filme",
  "tela",
  "live",
  "serie",
  "clipe",
  "musica",
  "musica",
  "conteudo",
  "programa",
  "algo",
  "coisa",
  "clip",
  "episodio",
  "trailer",
  "epis",
];

const VOICE_TITLE_SECTION_MARKER = "§§VOICE_SECTION§§";
const VOICE_TITLE_LOWERCASE_WORDS = new Set([
  "da",
  "de",
  "do",
  "das",
  "dos",
  "vs",
  "vs.",
  "x",
  "e",
  "and",
  "of",
  "the",
]);

const MAX_TEXT_CHANNELS = 8;

const VOICE_UI_TONES = {
  connect: { frequency: 660, duration: 0.18, volume: 0.14, wave: "triangle" },
  disconnect: { frequency: 420, duration: 0.2, volume: 0.12, wave: "sine" },
  share: { frequency: 520, duration: 0.22, volume: 0.16, wave: "sawtooth" },
};

const VOICE_TITLE_ACRONYM_WORDS = new Set(["AI", "IA", "VR", "HDR", "DLSS"]);

const PERSONALITY_LABEL_OVERRIDES = {
  IdentificacaoGeral: "Identificação Geral",
  AparenciaFisicaEstilo: "Aparência Física e Estilo",
  TraitsPersonalidade: "Traços de Personalidade",
  PsicologiaProfunda: "Psicologia Profunda",
  InteligenciaProcessamentoCognitivo: "Perfil Cognitivo",
  ComportamentoSocial: "Comportamento Social",
  Comunicacao: "Comunicação",
  ValoresEMoral: "Valores e Crenças",
  EstiloDeVida: "Rotina Psicossocial",
  RelacoesEAfetos: "Relações e Afeto",
  EmocoesEReacoes: "Perfil Emocional",
  HistoricoEExperiencias: "Experiências de Desenvolvimento",
  ObjetivosEProjecaoFutura: "Projeção de Vida",
  "FamiliaELaçosFamiliares": "Estrutura Familiar",
  Alimentacao: "Alimentação",
  Altura: "Altura",
  Apelidos: "Apelidos",
  ApelidosPai: "Apelidos do Pai",
  AssuntosQueEvitam: "Assuntos que Evitam",
  AtencaoFoco: "Atenção e Foco",
  Autoconfianca: "Autoconfiança",
  CapacidadeMemorizacao: "Capacidade de Memorização",
  CapacidadeNegociar: "Capacidade de Negociar",
  CausaOuIdeal: "Causa ou Ideal",
  ClasseSocialPercebida: "Classe Social Percebida",
  ComQuemMora: "Com quem Mora",
  ComoDesejaSerLembrado: "Como Deseja Ser Lembrada",
  ComposicaoFamiliarAtual: "Composição Familiar Atual",
  ConfiancaEmPessoas: "Confiança em Pessoas",
  ControleEmocional: "Controle Emocional",
  CorOlhos: "Cor dos Olhos",
  CorTipoCabelo: "Cor e Tipo de Cabelo",
  CostumesFamiliaresMantidos: "Costumes Familiares Mantidos",
  "CrençasCentraisSobreSiMesmo": "Crenças Centrais sobre Si Mesma",
  "CrençasSobreOMundo": "Crenças sobre o Mundo",
  "CrençasSobreOutrasPessoas": "Crenças sobre Outras Pessoas",
  DataNascimento: "Data de Nascimento",
  DefeitosPrincipais: "Defeitos Principais",
  DesejosMaisProfundos: "Desejos Mais Profundos",
  EmocaoMaisFrequente: "Emoção Mais Frequente",
  EstiloVestimenta: "Estilo de Vestimenta",
  EstrategiasDeEnfrentamento: "Estratégias de Enfrentamento",
  EventosFamiliaresMarcantesNegativos: "Eventos Familiares Marcantes (Negativos)",
  EventosFamiliaresMarcantesPositivos: "Eventos Familiares Marcantes (Positivos)",
  EventosMarcantesAdolescencia: "Eventos Marcantes da Adolescência",
  EventosMarcantesInfancia: "Eventos Marcantes da Infância",
  EventosMarcantesVidaAdulta: "Eventos Marcantes da Vida Adulta",
  ExpectativasFamiliares: "Expectativas Familiares",
  ExpectativasRelacionamentos: "Expectativas em Relacionamentos",
  Expressividade: "Expressividade",
  ExpressoesFaciaisComuns: "Expressões Faciais Comuns",
  FlexibilidadeMental: "Flexibilidade Mental",
  FormaDeAprenderMelhor: "Forma de Aprender Melhor",
  FormaDeContarHistorias: "Forma de Contar Histórias",
  FormaDeSeExpressarMelhor: "Forma de se Expressar Melhor",
  FormaDemonstrarAfeto: "Forma de Demonstrar Afeto",
  FormaLidarConflitos: "Forma de Lidar com Conflitos",
  FormaLidarTerminoAfastamento: "Forma de Lidar com Términos/Afastamentos",
  FormaSeApresentarEstranhos: "Como se Apresenta a Estranhos",
  FormasDeSeAcalmar: "Formas de se Acalmar",
  GatilhosEmocionais: "Gatilhos Emocionais",
  Genero: "Gênero",
  GestosCaracteristicos: "Gestos Característicos",
  HabilidadesAnaliticas: "Habilidades Analíticas",
  HerancaCulturalTradicoesFamiliares: "Herança Cultural e Tradições Familiares",
  HigienePessoal: "Higiene Pessoal",
  HistoriasNarrativasFamiliaresImportantes: "Histórias Familiares Importantes",
  HistoricoAmizadesAmoresImportantes: "Histórico de Amizades e Amores Importantes",
  HobbiesPassatempos: "Hobbies e Passatempos",
  HorarioMaiorEnergia: "Horário de Maior Energia",
  IdadeReal: "Idade Real",
  InfluenciasFamiliaresNasEscolhas: "Influências Familiares nas Escolhas",
  Insegurancas: "Inseguranças",
  InteressesCulinarios: "Interesses Culinários",
  LimitesPessoais: "Limites Pessoais",
  LinguagemCorporalPredominante: "Linguagem Corporal Predominante",
  LocalNascimento: "Local de Nascimento",
  LocalResidenciaAtual: "Local de Residência Atual",
  MarcasCicatrizes: "Marcas e Cicatrizes",
  MecanismosDeDefesa: "Mecanismos de Defesa",
  MedosFuturo: "Medos em Relação ao Futuro",
  MedosPrincipais: "Medos Principais",
  MetasCurtoPrazo: "Metas de Curto Prazo",
  MetasLongoPrazo: "Metas de Longo Prazo",
  MomentosMudaramFormaDePensar: "Momentos que Mudaram sua Forma de Pensar",
  Nacionalidade: "Nacionalidade",
  NecessidadeAprovacao: "Necessidade de Aprovação",
  NivelAtividadeFisica: "Nível de Atividade Física",
  NivelCiumes: "Nível de Ciúmes",
  NivelCuriosidade: "Nível de Curiosidade",
  NivelEmpatia: "Nível de Empatia",
  NivelExtroversaoIntroversao: "Nível de Extroversão/Introversão",
  NivelImpulsividade: "Nível de Impulsividade",
  NivelOtimismoPessimismo: "Nível de Otimismo/Pessimismo",
  NivelReligiosidadeEspiritualidade: "Nível de Religiosidade/Espiritualidade",
  NivelSinceridadeDiplomacia: "Nível de Sinceridade/Diplomacia",
  NivelSociabilidade: "Nível de Sociabilidade",
  NomeCompleto: "Nome Completo",
  NomeCompletoPai: "Nome Completo do Pai",
  ObjetivosDeVida: "Objetivos de Vida",
  Ocupacao: "Ocupação",
  PadroesDePensamentoRecorrentes: "Padrões de Pensamento Recorrentes",
  PapelComunEmGrupos: "Papel Comum em Grupos",
  PapelNaFamilia: "Papel na Família",
  Peso: "Peso",
  PlanosParaSuperar: "Planos para Superar",
  PosicionamentoPolitico: "Posicionamento Político",
  PosturaAndar: "Postura e Maneira de Andar",
  PreferenciaTrabalhoGrupoOuSozinho: "Preferência por Trabalho em Grupo ou Sozinha",
  PreferenciasDeLazer: "Preferências de Lazer",
  PreferenciasDeLeitura: "Preferências de Leitura",
  PreferenciasMusicais: "Preferências Musicais",
  PresencaFigMentorasInspiradoras: "Presença de Figuras Mentoras/Inspiradoras",
  PrincipaisConquistas: "Principais Conquistas",
  PrincipaisPerdas: "Principais Perdas",
  PrincipiosInegociaveis: "Princípios Inegociáveis",
  PronomePreferido: "Pronome Preferido",
  QualidadesPrincipais: "Qualidades Principais",
  ReacaoAoFracasso: "Reação ao Fracasso",
  ReacaoAoSucesso: "Reação ao Sucesso",
  ReacaoCriticas: "Reação a Críticas",
  ReacaoElogios: "Reação a Elogios",
  ReacaoSobPressao: "Reação sob Pressão",
  RegrasProprias: "Regras Próprias",
  RelacaoComIrmaos: "Relação com Irmãos",
  RelacaoComMae: "Relação com a Mãe",
  RelacaoComPai: "Relação com o Pai",
  RelacaoComTecnologia: "Relação com a Tecnologia",
  RotinaDiaria: "Rotina Diária",
  SensoDeHumor: "Senso de Humor",
  SituacoesGeramAnsiedade: "Situações que Geram Ansiedade",
  SituacoesGeramCalma: "Situações que Geram Calma",
  TendenciaGuardarExpressarEmocoes: "Tendência a Guardar ou Expressar Emoções",
  TipoCorpo: "Tipo de Corpo",
  TipoInteligenciaPredominante: "Tipo de Inteligência Predominante",
  TipoVinculoMaisValoriza: "Tipo de Vínculo que Mais Valoriza",
  ToleranciaEstresse: "Tolerância ao Estresse",
  TomDeVoz: "Tom de Voz",
  TomPele: "Tom de Pele",
  TranstornosCondicoesMentais: "Transtornos ou Condições Mentais",
  TraumasPassados: "Traumas Passados",
  UsoDeGirias: "Uso de Gírias",
  VelocidadeAoFalar: "Velocidade ao Falar",
  VelocidadeRaciocinio: "Velocidade de Raciocínio",
  ViagensExperienciasMarcantes: "Viagens e Experiências Marcantes",
  VisaoSobreCertoErrado: "Visão sobre Certo e Errado",
  VisaoSobreJustica: "Visão sobre Justiça",
  Vocabulario: "Vocabulário",
};

function normalizeIntentText(text) {
  if (!text) return "";
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[!?.,;:()/]+/g, " ")
    .replace(/\s+/g, " ")
    .toLowerCase()
    .trim();
}

function containsAny(text, tokens) {
  if (!text || !Array.isArray(tokens)) return false;
  return tokens.some((token) => token && text.includes(token));
}

const gifState = {
  gifs: [],
  filtered: [],
  isOpen: false,
  isLoading: false,
  hasLoaded: false,
  filter: "",
  isUploading: false,
};

const PROACTIVE_DELAYS = [60000, 120000, 240000];
const MAX_PROACTIVE_MESSAGES = 3;
const proactiveState = {
  timerId: null,
  attempt: 0,
  lastUserActivity: Date.now(),
  requestInFlight: false,
  proactiveMessagesSent: 0,
  absenceQuestionSent: false,
  awaitingUserResponse: false,
};
const louReplyState = {
  timerId: null,
  serverId: null,
  channelId: null,
  referenceMessage: null,
  debounceRange: { min: 5000, max: 7000 },
  generationToken: 0,
  abortController: null,
  outputController: null,
};
const AVAILABILITY_STATUS_META = {
  available: {
    label: "Disponível",
    toggleLabel: "Mudar para Ausente",
    cycleRange: { min: 60000, max: 600000 },
    responseLag: { min: 0, max: 1200 },
    typingLag: { min: 0, max: 600 },
  },
  away: {
    label: "Ausente",
    toggleLabel: "Mudar para Disponível",
    cycleRange: { min: 120000, max: 600000 },
    responseLag: { min: 3500, max: 7000 },
    typingLag: { min: 1500, max: 3200 },
  },
};
const AVAILABILITY_SHORT_CYCLE_RANGE = { min: 30000, max: 60000 };
const AVAILABILITY_SHORT_CYCLE_EXPIRY_MS = 10 * 60 * 1000;
const MANUAL_AWAY_DURATION_MS = { min: 120000, max: 600000 };
const AVAILABILITY_RETURN_COOLDOWN_MS = 5000;
const availabilityState = {
  status: "available",
  timerId: null,
  manualDowntimeTimerId: null,
  isManualDowntimeActive: false,
  pendingLouReply: null,
  cooldownUntil: 0,
  pendingShortCycle: false,
  lastUserMessageAt: 0,
  returnFromAwayTimerId: null,
};
const LOU_TYPING_INITIAL_DELAY = { min: 900, max: 2000 };
const LOU_TYPING_BURST_DELAY = { min: 1100, max: 2200 };
const LOU_TYPING_BETWEEN_DELAY = { min: 350, max: 900 };

function syncOverlayPresence() {
  const overlays = [
    elements.contextOverlay,
    elements.gifOverlay,
    elements.personalityOverlay,
  ];
  const hasVisibleOverlay =
    overlays.some((node) => node && !node.classList.contains("is-hidden")) || Boolean(modalState.node);
  if (document.body) {
    document.body.classList.toggle("has-overlay", hasVisibleOverlay);
  }
}

function setBinding(bindingNodes, value) {
  bindingNodes.forEach((node) => {
    node.textContent = value;
  });
}

function getActiveServer() {
  return state.servers.find((server) => server.id === state.activeServerId) ?? null;
}

function getActiveChannel() {
  const server = getActiveServer();
  if (!server) return null;
  return server.channels.find((channel) => channel.id === state.activeChannelId) ?? null;
}

function renderServers() {
  const rail = elements.serverRail;
  if (!rail) return;
  if (!rail) return;
  rail.innerHTML = "";
  const server = state.servers[0];
  if (!server) return;
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = server.shortName ?? server.name.slice(0, 2).toUpperCase();
  button.classList.add("active");
  button.title = server.name;
  button.addEventListener("click", () => {
    if (state.activeServerId === server.id) return;
    state.activeServerId = server.id;
    state.activeChannelId = server.channels[0]?.id ?? null;
    renderChannels();
    renderChatArea();
    refreshProactiveWatcher();
  });
  rail.appendChild(button);
}

function renderChannels() {
  const server = getActiveServer();
  setBinding(bindings.serverName, server?.name ?? "Grupo fixo");

  const list = elements.channelList;
  list.innerHTML = "";
  if (!server) {
    voiceState.channels = [];
    renderVoiceChannels();
    scheduleChannelLimitCheck(null);
    return;
  }

  server.channels.forEach((channel) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "channel-button";
    button.dataset.channelId = channel.id;
    if (channel.id === state.activeChannelId) button.classList.add("active");
    button.innerHTML = `
      <span class="channel-label">
        <span class="channel-badge">@</span>
        <span class="channel-name-text">${escapeHTML(channel.name)}</span>
      </span>
      <span class="channel-action-bar" aria-label="Ações do canal">
        <span class="channel-action" role="button" tabindex="0" data-channel-action="rename" title="Renomear canal">
          <i class="fas fa-pen-to-square" aria-hidden="true"></i>
        </span>
        <span class="channel-action" role="button" tabindex="0" data-channel-action="delete" title="Excluir canal">
          <i class="fas fa-trash" aria-hidden="true"></i>
        </span>
      </span>
    `;
    list.appendChild(button);
  });

  const voiceChannels = getVoiceChannelsForServer(server);
  voiceState.channels = voiceChannels;
  state.voiceChannels = voiceChannels;
  if (voiceState.activeChannelId && !voiceChannels.some((chn) => chn.id === voiceState.activeChannelId)) {
    leaveVoiceChannel({ silent: true });
  }
  renderVoiceChannels();
  renderVoicePresenceIndicator();
  syncVoiceControls();
  scheduleAiAutoLeaveIfNeeded();
  scheduleChannelLimitCheck(server);
}

function getVoiceChannelsForServer(server) {
  if (!server) return [];
  const firstChannel = Array.isArray(server.voice_channels) ? server.voice_channels[0] : null;
  const baseId = firstChannel?.id || `${server.id || "voice"}_chat`;
  return [{ id: baseId, name: "Chat de Voz" }];
}

function renderVoiceChannels() {
  if (!elements.voiceChannelList) return;
  elements.voiceChannelList.innerHTML = "";
  const channels = voiceState.channels ?? [];
  if (!channels.length) {
    const placeholder = document.createElement("p");
    placeholder.className = "voice-channel-status";
    placeholder.textContent = "Nenhum chat de voz disponível.";
    elements.voiceChannelList.appendChild(placeholder);
    return;
  }
  channels.forEach((channel) => {
    const isActive = channel.id === voiceState.activeChannelId;
    const aiInChannel = channel.id === voiceState.aiChannelId;
    const isAiStreaming = Boolean(
      aiInChannel && voiceState.share && voiceState.share.owner === "ai" && voiceState.share.channelId === channel.id
    );
    const statusLabel = isActive ? "Conectado" : "Entrar";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "voice-channel";
    if (isActive) button.classList.add("is-active");
    button.classList.toggle("has-ai", aiInChannel);
    button.classList.toggle("is-streaming", isAiStreaming);
    button.dataset.voiceChannelId = channel.id;
    button.innerHTML = `
      <span class="voice-channel-info">
        <i class="fas fa-volume-high" aria-hidden="true"></i>
        <span>${escapeHTML(channel.name)}</span>
      </span>
      <span class="voice-channel-status">${statusLabel}</span>
    `;
    elements.voiceChannelList.appendChild(button);
  });
}

function scheduleChannelLimitCheck(server) {
  if (typeof window === "undefined" || !window.requestAnimationFrame) {
    updateChannelCreationAvailability(server);
    return;
  }
  if (channelLimitMeasureFrame) {
    window.cancelAnimationFrame(channelLimitMeasureFrame);
  }
  channelLimitMeasureFrame = window.requestAnimationFrame(() => {
    channelLimitMeasureFrame = null;
    updateChannelCreationAvailability(server);
  });
}

function updateChannelCreationAvailability(server) {
  const button = elements.channelCreateButton;
  if (!button) return;
  if (!server) {
    button.disabled = true;
    button.title = "Selecione um servidor para criar canais";
    return;
  }
  const list = elements.channelList;
  if (!list) return;
  const maxChannelsReached =
    Array.isArray(server.channels) && server.channels.length >= MAX_TEXT_CHANNELS;
  const ranOutOfSpace = list.scrollHeight > list.clientHeight + 2;
  const reachedLimit = maxChannelsReached || ranOutOfSpace;
  button.disabled = reachedLimit;
  button.title = reachedLimit
    ? maxChannelsReached
  ? `Limite de ${MAX_TEXT_CHANNELS} chats atingido. Exclua um canal para liberar espaço.`
      : "Espaço esgotado acima do chat de voz. Exclua um canal para liberar espaço."
    : "Criar canal";
}

function handleVoiceChannelListClick(event) {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest("[data-voice-channel-id]");
  if (!button) return;
  const channelId = button.dataset.voiceChannelId;
  if (!channelId) return;
  if (voiceState.activeChannelId === channelId) {
    leaveVoiceChannel();
  } else {
    joinVoiceChannel(channelId);
  }
}

function joinVoiceChannel(channelId) {
  const channel = voiceState.channels.find((chn) => chn.id === channelId) || voiceState.channels[0];
  if (!channel) return;
  voiceState.activeChannelId = channel.id;
  voiceState.participants = [createVoiceParticipantFromProfile(profiles.user, "user")];
  if (voiceState.aiChannelId === channel.id) {
    ensureAiInParticipants();
  }
  renderVoiceChannels();
  showVoiceSession(channel);
  renderVoiceParticipants();
  renderVoiceShareFromState();
  restoreBackgroundedAiShareIfNeeded();
  renderVoicePresenceIndicator();
  syncVoiceControls();
  clearAiAutoLeaveTimer();
  playVoiceUiTone("connect");
}

function showVoiceSession(channel) {
  if (!elements.voiceSession) return;
  elements.voiceSession.classList.remove("is-hidden");
  if (elements.voiceSessionStatus) {
    elements.voiceSessionStatus.textContent = "";
  }
}

function renderVoiceParticipants() {
  if (!elements.voiceParticipants) return;
  elements.voiceParticipants.innerHTML = "";
  voiceState.participants.forEach((participant) => {
    const item = document.createElement("div");
    item.className = "voice-participant";
    const avatar = document.createElement("div");
    avatar.className = "voice-participant-avatar";
    if (participant.avatar) {
      const img = document.createElement("img");
      img.src = participant.avatar;
      img.alt = `Avatar de ${participant.name}`;
      avatar.appendChild(img);
    } else {
      avatar.textContent = participant.initials;
    }
    const textWrapper = document.createElement("div");
    const name = document.createElement("p");
    name.className = "voice-participant-name";
    name.textContent = participant.name;
    const role = document.createElement("p");
    role.className = "voice-participant-role";
    role.textContent = participant.roleLabel;
    textWrapper.append(name, role);
    item.append(avatar, textWrapper);
    elements.voiceParticipants.appendChild(item);
  });
}

function createVoiceParticipantFromProfile(profile, role) {
  const fallbackName = role === "ai" ? "Lou" : "Você";
  const name = profile?.name || fallbackName;
  const initialsSource = profile?.initials || name.slice(0, 2);
  const initials = initialsSource.toUpperCase();
  return {
    id: role,
    name,
    roleLabel: role === "ai" ? "IA" : "Você",
    avatar: profile?.avatar ? normalizeAssetPath(profile.avatar) : "",
    initials,
  };
}

function leaveVoiceChannel({ silent = false } = {}) {
  const wasUserStreaming = voiceState.share?.owner === "user";
  voiceState.activeChannelId = null;
  voiceState.participants = [];
  if (elements.voiceSession) {
    elements.voiceSession.classList.add("is-hidden");
  }
  if (!silent && elements.voiceSessionStatus) {
    elements.voiceSessionStatus.textContent = "";
  }
  if (wasUserStreaming) {
    stopVoiceShare();
  } else if (voiceState.share?.owner === "ai") {
    backgroundAiVoiceShare();
  } else {
    renderVoiceShareFromState();
  }
  renderVoiceChannels();
  renderVoicePresenceIndicator();
  syncVoiceControls();
  scheduleAiAutoLeaveIfNeeded();
  if (!silent) {
    playVoiceUiTone("disconnect");
  }
}

function syncVoiceControls() {
  const hasChannel = Boolean(voiceState.activeChannelId);
  const hasShare = Boolean(voiceState.share);
  const shareMatchesActive = Boolean(
    voiceState.share && voiceState.share.channelId === voiceState.activeChannelId
  );
  if (elements.voiceShareTrigger) {
    elements.voiceShareTrigger.classList.toggle("is-hidden", !hasChannel);
    elements.voiceShareTrigger.disabled = !hasChannel || hasShare;
  }
  if (elements.voiceShareStop) {
    const shouldShowStop = hasChannel && shareMatchesActive;
    elements.voiceShareStop.classList.toggle("is-hidden", !shouldShowStop);
    elements.voiceShareStop.disabled = !shouldShowStop;
  }
}

function pauseVoiceSharePlayback(removeSource = false) {
  if (!elements.voiceShareVideo) return;
  const videoEl = elements.voiceShareVideo;
  videoEl.pause();
  videoEl.currentTime = 0;
  videoEl.muted = true;
  videoEl.volume = 0;
  if (videoEl.srcObject) {
    videoEl.srcObject = null;
  }
  voicePlaybackState.pendingPlayPromise = null;
  if (removeSource) {
    videoEl.removeAttribute("src");
    videoEl.removeAttribute("data-voice-share-src");
    while (videoEl.firstChild) {
      videoEl.removeChild(videoEl.firstChild);
    }
    videoEl.load();
  }
  videoEl.removeAttribute("poster");
}

function hideVoiceShare({ clearState = true } = {}) {
  pauseVoiceSharePlayback(true);
  if (elements.voiceShareStatus && clearState) {
    elements.voiceShareStatus.textContent = "";
  }
  if (elements.voiceShare) {
    elements.voiceShare.classList.add("is-hidden");
  }
  clearVoiceShareReadyListeners();
  clearVoiceShareResumeOnInteraction();
  if (clearState) {
    clearVoiceShareUnmute();
  }
  if (clearState) {
    if (voiceState.share?.isObjectUrl && voiceState.share?.src) {
      try {
        URL.revokeObjectURL(voiceState.share.src);
      } catch (error) {
        console.warn("Falha ao liberar URL de transmissão", error);
      }
    }
    voiceState.share = null;
    voiceState.isShareMinimized = false;
    voiceState.aiShareBackgrounded = false;
    renderVoicePresenceIndicator();
    renderVoiceChannels();
  }
  updateVoiceShareVisibilityUi();
  syncVoiceControls();
}

function scheduleVoiceShareUnmute() {
  clearVoiceShareUnmute();
  voicePlaybackState.unmuteTimerId = window.setTimeout(() => {
    voicePlaybackState.unmuteTimerId = null;
    if (!voiceState.share || voiceState.share.owner !== "ai") return;
    if (!elements.voiceShareVideo) return;
    elements.voiceShareVideo.muted = false;
    elements.voiceShareVideo.volume = 1;
    if (
      elements.voiceShareStatus &&
      voiceState.activeChannelId &&
      voiceState.share.channelId === voiceState.activeChannelId
    ) {
      elements.voiceShareStatus.textContent = "Lou está transmitindo";
    }
  }, 600);
}

function clearVoiceShareUnmute() {
  if (voicePlaybackState.unmuteTimerId) {
    window.clearTimeout(voicePlaybackState.unmuteTimerId);
    voicePlaybackState.unmuteTimerId = null;
  }
}

function requestVoiceShareResumeOnInteraction(callback) {
  clearVoiceShareResumeOnInteraction();
  if (typeof callback !== "function") return;
  const handler = () => {
    clearVoiceShareResumeOnInteraction();
    callback();
  };
  voicePlaybackState.resumeOnInteractHandler = handler;
  document.addEventListener("pointerdown", handler, { once: true });
  document.addEventListener("keydown", handler, { once: true });
}

function clearVoiceShareResumeOnInteraction() {
  if (!voicePlaybackState.resumeOnInteractHandler) return;
  document.removeEventListener("pointerdown", voicePlaybackState.resumeOnInteractHandler);
  document.removeEventListener("keydown", voicePlaybackState.resumeOnInteractHandler);
  voicePlaybackState.resumeOnInteractHandler = null;
}

function clearVoiceShareReadyListeners() {
  if (!elements.voiceShareVideo) return;
  if (voicePlaybackState.readyHandler) {
    elements.voiceShareVideo.removeEventListener("canplay", voicePlaybackState.readyHandler);
    voicePlaybackState.readyHandler = null;
  }
  if (voicePlaybackState.readyErrorHandler) {
    elements.voiceShareVideo.removeEventListener("error", voicePlaybackState.readyErrorHandler);
    voicePlaybackState.readyErrorHandler = null;
  }

  updateVoiceShareVisibilityUi();
}

function removeAiFromParticipants() {
  const before = voiceState.participants.length;
  voiceState.participants = voiceState.participants.filter((participant) => participant.id !== "ai");
  return voiceState.participants.length !== before;
}

function clearAiAutoLeaveTimer() {
  if (voiceTimers.aiAutoLeaveTimeoutId) {
    window.clearTimeout(voiceTimers.aiAutoLeaveTimeoutId);
    voiceTimers.aiAutoLeaveTimeoutId = null;
  }
}

function scheduleAiAutoLeaveIfNeeded() {
  clearAiAutoLeaveTimer();
  if (!voiceState.aiChannelId) return;
  const userInSameChannel = Boolean(
    voiceState.activeChannelId && voiceState.activeChannelId === voiceState.aiChannelId
  );
  if (userInSameChannel) return;
  voiceTimers.aiAutoLeaveTimeoutId = window.setTimeout(() => {
    voiceTimers.aiAutoLeaveTimeoutId = null;
    disconnectAiFromVoiceChannel({ reason: "idle" });
  }, AI_AUTO_LEAVE_DELAY_MS);
}

function disconnectAiFromVoiceChannel({ reason = "manual" } = {}) {
  if (!voiceState.aiChannelId) return;
  const channelId = voiceState.aiChannelId;
  clearAiAutoLeaveTimer();
  const aiStreamingInChannel = Boolean(
    voiceState.share && voiceState.share.owner === "ai" && voiceState.share.channelId === channelId
  );
  if (aiStreamingInChannel) {
    stopVoiceShare();
    clearAiAutoLeaveTimer();
  }
  const removed = removeAiFromParticipants();
  clearAiPresence();
  if (removed) {
    renderVoiceParticipants();
  }
  renderVoicePresenceIndicator();
  renderVoiceChannels();
  if (elements.voiceSessionStatus) {
    if (reason === "idle") {
      elements.voiceSessionStatus.textContent = "Lou saiu do chat de voz por inatividade";
    } else if (reason === "manual" && voiceState.activeChannelId === channelId) {
      elements.voiceSessionStatus.textContent = "Lou saiu do chat de voz";
    }
  }
}

function ensureVoicePlaybackUnlock() {
  if (voicePlaybackState.isUnlocked) return Promise.resolve();
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (typeof AudioContextClass === "function") {
    if (!voicePlaybackState.audioContext) {
      try {
        voicePlaybackState.audioContext = new AudioContextClass();
      } catch (error) {
        console.warn("Não foi possível criar AudioContext para desbloqueio", error);
      }
    }
    const context = voicePlaybackState.audioContext;
    if (context && context.state === "suspended") {
      return context
        .resume()
        .then(() => {
          voicePlaybackState.isUnlocked = true;
        })
        .catch((error) => {
          console.warn("Falha ao retomar AudioContext", error);
          voicePlaybackState.isUnlocked = true;
        });
    }
    if (context && context.state === "running") {
      voicePlaybackState.isUnlocked = true;
      return Promise.resolve();
    }
  }
  voicePlaybackState.isUnlocked = true;
  return Promise.resolve();
}

function setupVoicePlaybackUnlockListeners() {
  if (voicePlaybackState.unlockListenersAttached) return;
  const unlock = () => {
    ensureVoicePlaybackUnlock();
  };
  document.addEventListener("pointerdown", unlock, { once: true });
  document.addEventListener("keydown", unlock, { once: true });
  voicePlaybackState.unlockListenersAttached = true;
}

function playVoiceUiTone(kind) {
  const tone = VOICE_UI_TONES[kind];
  if (!tone) return;
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (typeof AudioContextClass !== "function") return;
  if (!voicePlaybackState.audioContext) {
    try {
      voicePlaybackState.audioContext = new AudioContextClass();
    } catch (error) {
      console.warn("Não foi possível inicializar AudioContext para tons de voz", error);
      return;
    }
  }
  const context = voicePlaybackState.audioContext;
  ensureVoicePlaybackUnlock();
  const oscillator = context.createOscillator();
  const gainNode = context.createGain();
  oscillator.type = tone.wave || tone.type || "sine";
  oscillator.frequency.setValueAtTime(tone.frequency || 600, context.currentTime);
  const now = context.currentTime;
  const duration = Math.max(0.08, tone.duration || 0.18);
  const peak = Math.max(0.01, tone.volume || 0.12);
  gainNode.gain.setValueAtTime(0.0001, now);
  gainNode.gain.exponentialRampToValueAtTime(peak, now + 0.01);
  gainNode.gain.exponentialRampToValueAtTime(0.0001, now + duration);
  oscillator.connect(gainNode);
  gainNode.connect(context.destination);
  oscillator.start(now);
  oscillator.stop(now + duration);
  oscillator.addEventListener("ended", () => {
    try {
      oscillator.disconnect();
      gainNode.disconnect();
    } catch (error) {
      console.warn("Falha ao liberar nodes de áudio", error);
    }
  });
}

function stopVoiceShare({ userTriggered = false } = {}) {
  if (!voiceState.share) return;
  const shareOwner = voiceState.share.owner;
  hideVoiceShare({ clearState: true });
  scheduleAiAutoLeaveIfNeeded();
  if (!elements.voiceSessionStatus || !voiceState.activeChannelId) return;
  if (shareOwner === "ai") {
    elements.voiceSessionStatus.textContent = userTriggered
      ? "Transmissão da Lou encerrada"
      : "Lou encerrou a transmissão";
  } else {
    elements.voiceSessionStatus.textContent = "Transmissão encerrada";
  }
}

function connectAiToVoiceChannel(channel, { source = "auto" } = {}) {
  if (!channel) return;
  voiceState.aiChannelId = channel.id;
  voiceState.aiPresenceSource = source;
  if (voiceState.activeChannelId === channel.id) {
    ensureAiInParticipants();
    renderVoiceParticipants();
  }
  renderVoicePresenceIndicator();
  renderVoiceChannels();
  scheduleAiAutoLeaveIfNeeded();
}

function ensureAiInParticipants() {
  if (voiceState.participants.some((participant) => participant.id === "ai")) return;
  voiceState.participants.push(createVoiceParticipantFromProfile(profiles.model, "ai"));
}

function renderVoicePresenceIndicator() {
  const indicator = elements.voicePresenceIndicator;
  if (!indicator) return;
  const channel = voiceState.channels.find((chn) => chn.id === voiceState.aiChannelId);
  const shouldShow = Boolean(channel && voiceState.activeChannelId !== channel.id);
  indicator.classList.toggle("is-hidden", !shouldShow);
  if (shouldShow) {
    const label = indicator.querySelector("span");
    if (label) {
      const isStreaming = Boolean(
        voiceState.share &&
          voiceState.share.owner === "ai" &&
          voiceState.share.channelId === channel.id
      );
      label.textContent = isStreaming
        ? `Lou está transmitindo em ${channel.name}`
        : `Lou está em ${channel.name}`;
    }
  }
}

function clearAiPresence() {
  voiceState.aiChannelId = null;
  voiceState.aiPresenceSource = null;
}

function setVoiceShareState(shareConfig = {}) {
  const previousShare = voiceState.share;
  hideVoiceShare({ clearState: true });
  const channelId =
    shareConfig.channelId ||
    voiceState.activeChannelId ||
    voiceState.aiChannelId ||
    voiceState.channels[0]?.id ||
    null;
  if (!channelId) {
    console.warn("Nenhum canal disponível para transmitir");
    return;
  }
  voiceState.share = { ...shareConfig, channelId };
  const shareOwner = voiceState.share.owner;
  const shareChannelId = voiceState.share.channelId;
  const shareSrc = voiceState.share.src;
  const shouldPlayTone =
    !previousShare ||
    previousShare.owner !== shareOwner ||
    previousShare.channelId !== shareChannelId ||
    previousShare.src !== shareSrc;
  voiceState.isShareMinimized = false;
  voiceState.aiShareBackgrounded = false;
  renderVoiceShareFromState();
  renderVoicePresenceIndicator();
  renderVoiceChannels();
  syncVoiceControls();
  if (shouldPlayTone) {
    playVoiceUiTone("share");
  }
}

function resetVoiceShareVideoElement(videoEl) {
  if (!videoEl) return;
  videoEl.pause();
  videoEl.removeAttribute("src");
  while (videoEl.firstChild) {
    videoEl.removeChild(videoEl.firstChild);
  }
  videoEl.load();
}

function inferMimeTypeFromSource(source) {
  if (!source) return "video/mp4";
  const lowercase = source.split("?")[0].toLowerCase();
  if (lowercase.endsWith(".webm")) return "video/webm";
  if (lowercase.endsWith(".ogv") || lowercase.endsWith(".ogg")) return "video/ogg";
  if (lowercase.endsWith(".mov")) return "video/quicktime";
  if (lowercase.endsWith(".mkv")) return "video/x-matroska";
  if (lowercase.endsWith(".m4v")) return "video/x-m4v";
  return "video/mp4";
}

function applyVoiceShareSources(videoEl, share) {
  if (!videoEl || !share?.src) return;
  const sourceNode = document.createElement("source");
  sourceNode.src = share.src;
  const mimeType = share.mimeType || inferMimeTypeFromSource(share.src);
  if (mimeType) {
    sourceNode.type = mimeType;
  }
  videoEl.appendChild(sourceNode);
  videoEl.setAttribute("data-voice-share-src", share.src);
  videoEl.load();
}

function formatVoiceShareTitle(rawTitle) {
  if (!rawTitle) return "Transmissão";
  const marker = VOICE_TITLE_SECTION_MARKER;
  const withoutExt = rawTitle.replace(/\.[a-z0-9]+$/i, "");
  const underscoreNormalized = withoutExt.replace(/_/g, " ");
  let normalized = underscoreNormalized
    .replace(/-[_\s]*-/g, ` ${marker} `)
    .replace(/\s-\s/g, ` ${marker} `)
    .replace(/-/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim();
  if (!normalized) {
    return "Transmissão";
  }
  const rawSegments = normalized.includes(marker)
    ? normalized
        .split(marker)
        .map((segment) => segment.trim())
        .filter(Boolean)
    : [normalized];
  const formattedSegments = rawSegments
    .map((segment) => formatVoiceTitleSegment(segment))
    .filter(Boolean);
  const result = formattedSegments.join(" - ").replace(/\s{2,}/g, " ").trim();
  return result || normalized || "Transmissão";
}

function formatVoiceTitleSegment(segment) {
  if (!segment) return "";
  const words = segment
    .split(/\s+/)
    .map((word) => word.trim())
    .filter(Boolean);
  const formatted = words
    .map((word, index) => formatVoiceTitleWord(word, index))
    .filter(Boolean)
    .join(" ")
    .replace(/\s{2,}/g, " ")
    .trim();
  return formatted;
}

function formatVoiceTitleWord(word, index) {
  if (!word) return "";
  const stripped = word
    .replace(/^[^0-9A-Za-zÀ-ÿçÇ]+/, "")
    .replace(/[^0-9A-Za-zÀ-ÿçÇ.]+$/, "");
  if (!stripped) return "";
  if (/^\d+$/.test(stripped)) {
    return stripped;
  }
  if (/^(x|vs|vs\.)$/i.test(stripped)) {
    return "vs";
  }
  if (/^[ivxlcdm]+$/i.test(stripped)) {
    return stripped.toUpperCase();
  }
  if (VOICE_TITLE_ACRONYM_WORDS.has(stripped.toUpperCase())) {
    return stripped.toUpperCase();
  }
  const lower = stripped.toLowerCase();
  if (VOICE_TITLE_LOWERCASE_WORDS.has(lower) && index !== 0) {
    return lower.replace("vs.", "vs");
  }
  if (stripped.length <= 3 && stripped === stripped.toUpperCase()) {
    return stripped;
  }
  return stripped.charAt(0).toUpperCase() + stripped.slice(1).toLowerCase();
}

function setVoiceShareMinimized(hidden) {
  voiceState.isShareMinimized = Boolean(hidden);
  updateVoiceShareVisibilityUi();
}

function updateVoiceShareVisibilityUi() {
  if (!elements.voiceShare) return;
  elements.voiceShare.classList.toggle("is-collapsed", Boolean(voiceState.isShareMinimized));
  const toggle = elements.voiceShareToggle;
  if (toggle) {
    toggle.setAttribute("aria-pressed", voiceState.isShareMinimized ? "true" : "false");
    const icon = toggle.querySelector("i");
    const label = toggle.querySelector("span");
    if (icon) {
      icon.className = `fas ${voiceState.isShareMinimized ? "fa-eye" : "fa-eye-slash"}`;
    }
    if (label) {
      label.textContent = voiceState.isShareMinimized ? "Mostrar" : "Ocultar";
    }
  }
  if (elements.voiceShareCollapseBanner) {
    elements.voiceShareCollapseBanner.classList.toggle("is-hidden", !voiceState.isShareMinimized);
  }
}

function handleVoiceShareToggleClick() {
  setVoiceShareMinimized(!voiceState.isShareMinimized);
}

function handleVoiceShareCollapseBannerClick() {
  setVoiceShareMinimized(false);
}

function backgroundAiVoiceShare() {
  voiceState.aiShareBackgrounded = Boolean(voiceState.share && voiceState.share.owner === "ai");
  if (!voiceState.aiShareBackgrounded) return;
  if (elements.voiceShareVideo) {
    elements.voiceShareVideo.muted = true;
    elements.voiceShareVideo.volume = 0;
    elements.voiceShareVideo.setAttribute("muted", "muted");
  }
  if (elements.voiceShare) {
    elements.voiceShare.classList.add("is-hidden");
  }
}

function restoreBackgroundedAiShareIfNeeded() {
  if (!voiceState.aiShareBackgrounded) return;
  if (!voiceState.share || voiceState.share.owner !== "ai") {
    voiceState.aiShareBackgrounded = false;
    return;
  }
  const sameChannel = Boolean(
    voiceState.activeChannelId && voiceState.share.channelId === voiceState.activeChannelId
  );
  if (!sameChannel) return;
  voiceState.aiShareBackgrounded = false;
  scheduleVoiceShareUnmute();
}

function renderVoiceShareFromState() {
  const share = voiceState.share;
  if (!share) {
    hideVoiceShare({ clearState: true });
    return;
  }
  if (!elements.voiceShare || !elements.voiceShareVideo) return;
  const canDisplay = Boolean(
    voiceState.activeChannelId && share.channelId === voiceState.activeChannelId
  );
  if (!canDisplay) {
    if (share.owner === "ai") {
      elements.voiceShare.classList.add("is-hidden");
      return;
    }
    hideVoiceShare({ clearState: false });
    return;
  }
  elements.voiceShare.classList.remove("is-hidden");
  clearVoiceShareResumeOnInteraction();
  clearVoiceShareReadyListeners();
  if (elements.voiceShareTitle) {
    elements.voiceShareTitle.textContent = formatVoiceShareTitle(share.title);
  }
  if (elements.voiceShareStatus) {
    elements.voiceShareStatus.textContent = share.owner === "ai" ? "Lou está transmitindo" : "Você está transmitindo";
  }
  const videoEl = elements.voiceShareVideo;
  const previousSrc = videoEl.getAttribute("data-voice-share-src") || videoEl.getAttribute("src") || "";
  const needsUpdate = previousSrc !== share.src;
  if (needsUpdate) {
    resetVoiceShareVideoElement(videoEl);
    applyVoiceShareSources(videoEl, share);
    videoEl.src = share.src;
    videoEl.currentTime = 0;
  }
  const shouldStartMuted = share.owner === "ai";
  videoEl.autoplay = true;
  videoEl.setAttribute("autoplay", "autoplay");
  videoEl.playsInline = true;
  videoEl.setAttribute("playsinline", "playsinline");
  videoEl.preload = "auto";
  videoEl.crossOrigin = "anonymous";
  videoEl.muted = shouldStartMuted;
  if (shouldStartMuted) {
    videoEl.setAttribute("muted", "muted");
  } else {
    videoEl.removeAttribute("muted");
  }
  videoEl.volume = 1;

  const startPlayback = () => {
    Promise.resolve(ensureVoicePlaybackUnlock())
      .catch(() => {})
      .finally(() => {
        const playPromise = videoEl.play();
        voicePlaybackState.pendingPlayPromise = playPromise ?? null;
        if (playPromise?.then) {
          playPromise
            .then(() => {
              voicePlaybackState.pendingPlayPromise = null;
              clearVoiceShareResumeOnInteraction();
              if (shouldStartMuted) {
                scheduleVoiceShareUnmute();
              }
            })
            .catch((error) => {
              voicePlaybackState.pendingPlayPromise = null;
              if (shouldStartMuted && !videoEl.muted) {
                videoEl.muted = true;
                videoEl.setAttribute("muted", "muted");
                startPlayback();
                return;
              }
              console.warn("Não foi possível iniciar a transmissão automaticamente", error);
              requestVoiceShareResumeOnInteraction(startPlayback);
            });
        } else if (shouldStartMuted) {
          scheduleVoiceShareUnmute();
        }
      });
  };

  if (!needsUpdate && videoEl.readyState >= 2) {
    startPlayback();
  } else {
    const handleReady = () => {
      clearVoiceShareReadyListeners();
      startPlayback();
    };
    const handleError = (event) => {
      clearVoiceShareReadyListeners();
      console.error("Falha ao preparar transmissão da Lou", event?.error || event);
    };
    voicePlaybackState.readyHandler = handleReady;
    voicePlaybackState.readyErrorHandler = handleError;
    videoEl.addEventListener("canplay", handleReady);
    videoEl.addEventListener("error", handleError);
    videoEl.load();
  }
}

async function startAiVoiceShare(channel) {
  if (!channel) return;
  const library = await ensureVoiceMediaLibrary();
  if (!library.length) {
    if (elements.voiceSessionStatus && voiceState.activeChannelId === channel.id) {
      elements.voiceSessionStatus.textContent = "Nenhum vídeo encontrado em assets/videos";
    }
    return;
  }
  const chosen = pickRandomVoiceVideo(library);
  if (!chosen) return;
  setVoiceShareState({
    owner: "ai",
    title: chosen.filename || "Transmissão surpresa",
    src: normalizeAssetPath(chosen.path || chosen.filename),
    isObjectUrl: false,
    channelId: channel.id,
    mimeType: inferMimeTypeFromSource(chosen.path || chosen.filename || ""),
  });
}

async function requestAiTransmission({ channelId } = {}) {
  const channel =
    voiceState.channels.find((chn) => chn.id === channelId) ||
    voiceState.channels.find((chn) => chn.id === voiceState.activeChannelId) ||
    voiceState.channels[0];
  if (!channel) return;
  if (voiceState.aiChannelId !== channel.id) {
    connectAiToVoiceChannel(channel, { source: "summoned" });
  }
  await startAiVoiceShare(channel);
}

async function ensureVoiceMediaLibrary(force = false) {
  if (voiceMediaLibrary.items.length && !force) {
    return voiceMediaLibrary.items;
  }
  if (voiceMediaLibrary.isLoading && voiceMediaLibrary.promise) {
    await voiceMediaLibrary.promise;
    return voiceMediaLibrary.items;
  }
  voiceMediaLibrary.isLoading = true;
  voiceMediaLibrary.promise = fetchVoiceMediaLibrary();
  try {
    voiceMediaLibrary.items = await voiceMediaLibrary.promise;
    voiceMediaLibrary.lastLoadedAt = Date.now();
  } finally {
    voiceMediaLibrary.isLoading = false;
    voiceMediaLibrary.promise = null;
  }
  return voiceMediaLibrary.items;
}

async function fetchVoiceMediaLibrary() {
  try {
    const response = await fetch(`${API_BASE}/media/videos`);
    if (!response.ok) throw new Error("Falha ao listar vídeos");
    const payload = await response.json();
    return Array.isArray(payload?.videos) ? payload.videos : [];
  } catch (error) {
    console.error("Erro ao carregar lista de vídeos", error);
    return [];
  }
}

function pickRandomVoiceVideo(items) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) return null;
  const index = Math.floor(Math.random() * list.length);
  return list[index];
}

function handleVoiceShareTriggerClick() {
  if (!voiceState.activeChannelId) {
    if (elements.voiceSessionStatus) {
      elements.voiceSessionStatus.textContent = "Entre no chat de voz para iniciar uma transmissão.";
    }
    return;
  }
  if (voiceState.share) return;
  if (!elements.voiceShareFileInput) return;
  elements.voiceShareFileInput.value = "";
  elements.voiceShareFileInput.click();
}

function handleVoiceShareFileChange(event) {
  const file = event.target?.files?.[0];
  if (!file) return;
  startUserVoiceShare(file);
}

function startUserVoiceShare(file) {
  if (!voiceState.activeChannelId) return;
  const objectUrl = URL.createObjectURL(file);
  setVoiceShareState({
    owner: "user",
    title: file.name || "Minha transmissão",
    src: objectUrl,
    isObjectUrl: true,
    mimeType: file.type || inferMimeTypeFromSource(file.name || ""),
    channelId: voiceState.activeChannelId,
  });
}

function handleVoiceShareStopClick() {
  stopVoiceShare({ userTriggered: true });
}

function analyzeVoiceIntentsFromMessage(content, context = {}) {
  const normalized = normalizeIntentText(content);
  if (!normalized) return;
  if (matchesVoiceJoinIntent(normalized)) {
    handleVoiceJoinIntent(context);
  }
  if (matchesVoiceShareIntent(normalized)) {
    handleVoiceShareIntent(context);
  }
}

function matchesVoicePattern(normalizedText, patterns) {
  if (!normalizedText) return false;
  return patterns.some((regex) => regex.test(normalizedText));
}

function matchesVoiceJoinIntent(text) {
  if (matchesVoicePattern(text, VOICE_JOIN_PATTERNS)) return true;
  const hasVoiceWord = containsAny(text, VOICE_CHANNEL_TERMS);
  const hasJoinVerb = containsAny(text, VOICE_JOIN_VERBS);
  const mentionsLou = containsAny(text, VOICE_SUMMON_TERMS);
  if ((hasVoiceWord && hasJoinVerb) || (mentionsLou && hasVoiceWord) || (mentionsLou && hasJoinVerb)) {
    return true;
  }
  if (text.includes("vem pra chamada") || text.includes("vem pra call")) {
    return true;
  }
  return false;
}

function matchesVoiceShareIntent(text) {
  if (matchesVoicePattern(text, VOICE_SHARE_PATTERNS)) return true;
  const hasShareVerb = containsAny(text, VOICE_SHARE_VERBS);
  const hasMediaTerm = containsAny(text, VOICE_MEDIA_TERMS);
  const hasVoiceWord = containsAny(text, VOICE_CHANNEL_TERMS);
  const mentionsLou = containsAny(text, VOICE_SUMMON_TERMS);
  return (
    (hasShareVerb && (hasMediaTerm || hasVoiceWord)) ||
    (mentionsLou && hasShareVerb) ||
    (hasShareVerb && text.includes("pra mim"))
  );
}

function queueVoiceIntentAction(action = {}) {
  if (!action.channelId || !action.type) return;
  const entry = {
    id: `voice-intent-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    type: action.type,
    channelId: action.channelId,
    serverId: action.serverId ?? null,
    originChannelId: action.originChannelId ?? null,
    delayMs: action.delayMs ?? VOICE_ACTION_DELAY_MS,
  };
  voiceIntentState.pending.push(entry);
}

function flushVoiceIntentQueue(serverId, channelId) {
  if (!channelId || !voiceIntentState.pending.length) return;
  const actions = [];
  voiceIntentState.pending = voiceIntentState.pending.filter((action) => {
    const sameVoiceChannel = action.channelId === channelId;
    const sameServer = !serverId || !action.serverId || action.serverId === serverId;
    const sameOrigin = !action.originChannelId || action.originChannelId === channelId;
    if ((sameVoiceChannel || sameOrigin) && sameServer) {
      actions.push(action);
      return false;
    }
    return true;
  });
  if (!actions.length) return;
  processVoiceIntentActionsSequentially(actions);
}

function processVoiceIntentActionsSequentially(actions) {
  actions.reduce((chain, action) => {
    return chain
      .then(() => delay(action.delayMs ?? VOICE_ACTION_DELAY_MS))
      .then(() => executeVoiceIntentAction(action))
      .catch((error) => {
        console.error("Falha ao executar ação de voz", error);
      });
  }, Promise.resolve());
}

function executeVoiceIntentAction(action) {
  if (!action || !action.type) return Promise.resolve();
  if (action.type === "join") {
    return executeVoiceJoinAction(action);
  }
  if (action.type === "share") {
    return executeVoiceShareAction(action);
  }
  return Promise.resolve();
}

async function executeVoiceJoinAction(action) {
  const channel = voiceState.channels.find((chn) => chn.id === action.channelId) || voiceState.channels[0];
  if (!channel) return;
  const alreadyInChannel = voiceState.aiChannelId === channel.id;
  if (alreadyInChannel) {
    if (elements.voiceSessionStatus && voiceState.activeChannelId === channel.id) {
      elements.voiceSessionStatus.textContent = "Lou já está no chat de voz";
    }
    return;
  }
  if (elements.voiceSessionStatus && voiceState.activeChannelId === channel.id) {
    elements.voiceSessionStatus.textContent = "Lou está entrando no chat de voz...";
  }
  connectAiToVoiceChannel(channel, { source: "summoned" });
  if (elements.voiceSessionStatus && voiceState.activeChannelId === channel.id) {
    elements.voiceSessionStatus.textContent = "Lou entrou no chat de voz";
  }
}

async function executeVoiceShareAction(action) {
  const channel = voiceState.channels.find((chn) => chn.id === action.channelId) || voiceState.channels[0];
  if (!channel) return;
  const alreadyInChannel = voiceState.aiChannelId === channel.id;
  if (!alreadyInChannel && elements.voiceSessionStatus && voiceState.activeChannelId === channel.id) {
    elements.voiceSessionStatus.textContent = "Lou está entrando no chat de voz...";
  }
  if (alreadyInChannel && elements.voiceSessionStatus && voiceState.activeChannelId === channel.id) {
    elements.voiceSessionStatus.textContent = "Lou vai iniciar uma transmissão";
  }
  try {
    await requestAiTransmission({ channelId: channel.id });
    if (elements.voiceSessionStatus && voiceState.activeChannelId === channel.id) {
      elements.voiceSessionStatus.textContent = "Lou iniciou uma transmissão";
    }
  } catch (error) {
    console.error("Não foi possível iniciar a transmissão da Lou", error);
    if (elements.voiceSessionStatus && voiceState.activeChannelId === channel.id) {
      elements.voiceSessionStatus.textContent = "Falha ao iniciar transmissão da Lou";
    }
  }
}

function handleVoiceJoinIntent(context = {}) {
  const channelId = voiceState.activeChannelId || voiceState.channels[0]?.id || null;
  if (!channelId) return;
  queueVoiceIntentAction({
    type: "join",
    channelId,
    serverId: context.serverId,
    originChannelId: context.channelId ?? state.activeChannelId,
  });
  if (elements.voiceSessionStatus && voiceState.activeChannelId === channelId) {
    elements.voiceSessionStatus.textContent = "Lou vai entrar assim que responder";
  }
}

function handleVoiceShareIntent(context = {}) {
  const channelId = voiceState.activeChannelId || voiceState.channels[0]?.id || null;
  if (!channelId) return;
  queueVoiceIntentAction({
    type: "share",
    channelId,
    serverId: context.serverId,
    originChannelId: context.channelId ?? state.activeChannelId,
  });
  if (elements.voiceSessionStatus && voiceState.activeChannelId === channelId) {
    elements.voiceSessionStatus.textContent = "Lou vai preparar uma transmissão";
  }
}

function renderChatArea() {
  const channel = getActiveChannel();
  if (!channel || channel.id !== replyState.channelId) {
    clearReplyTarget();
  }
  const channelHandle = channel ? formatChannelHandle(channel.name) : null;
  setBinding(bindings.channelName, channel ? channelHandle : "Selecione um canal");
  setBinding(bindings.channelTopic, channel?.topic ?? "");
  updateComposerPlaceholders(channel);
  renderMessages();
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatChannelHandle(name) {
  const cleaned = (name || "").replace(/^[@#]+/, "").trim();
  return cleaned ? `@ ${cleaned}` : "@ canal";
}

function updateComposerPlaceholders(channel) {
  const handle = channel ? formatChannelHandle(channel.name) : null;
  const mainPlaceholder = channel ? `Conversar em ${handle}` : "Selecione um canal";
  if (elements.messageInput) {
    elements.messageInput.placeholder = mainPlaceholder;
  }
}

function renderMessages() {
  const channel = getActiveChannel();
  const container = elements.messageList;
  container.innerHTML = "";
  if (state.isLoading) {
    showEmptyState("Carregando", "Buscando dados no backend local...");
    return;
  }
  if (!channel) {
  showEmptyState("Nenhum chat selecionado", "Crie um chat para iniciar a conversa.");
    return;
  }

  let lastDayLabel = "";
  if (channel.messages.length === 0) {
  showEmptyState("Sem histórico", "Envie uma mensagem para iniciar a conversa.");
    return;
  }

  hideEmptyState();
  channel.messages.forEach((message) => {
    const currentDayLabel = formatDay(message.timestamp);
    if (currentDayLabel !== lastDayLabel) {
      const dayDivider = document.createElement("p");
      dayDivider.className = "day-separator";
      dayDivider.textContent = currentDayLabel;
      container.appendChild(dayDivider);
      lastDayLabel = currentDayLabel;
    }
    container.appendChild(createMessageNode(message, channel.messages));
  });
  container.scrollTop = container.scrollHeight;
}

function randomBetween(min, max) {
  const lower = Math.min(min, max);
  const upper = Math.max(min, max);
  return Math.floor(Math.random() * (upper - lower + 1)) + lower;
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, ms)));
}

function getAvailabilityConfig(status) {
  return AVAILABILITY_STATUS_META[status] ?? AVAILABILITY_STATUS_META.available;
}

function initAiAvailability() {
  setAiAvailability(availabilityState.status);
}

function setAiAvailability(nextStatus, options = {}) {
  const normalized = AVAILABILITY_STATUS_META[nextStatus] ? nextStatus : "available";
  const previousStatus = availabilityState.status;
  if (!options.preserveTimer) {
    clearAvailabilityShiftTimer();
  }
  clearReturnFromAwayTimer();
  availabilityState.status = normalized;
  if (normalized === "available" && previousStatus === "away") {
    availabilityState.cooldownUntil = Date.now() + AVAILABILITY_RETURN_COOLDOWN_MS;
  }
  if (normalized === "away") {
    availabilityState.cooldownUntil = 0;
  }
  updateAiAvailabilityUi();
  if (normalized === "available") {
    dispatchPendingLouReply();
  }
  if (options.skipSchedule) {
    return;
  }
  scheduleAvailabilityShift();
}

function updateAiAvailabilityUi() {
  const indicator = elements.aiAvailability;
  const labelNode = elements.aiAvailabilityLabel;
  const toggleLabelNode = elements.availabilityToggleLabel;
  const toggleButton = elements.availabilityToggle;
  const toggleDot = elements.availabilityToggleDot;
  const config = getAvailabilityConfig(availabilityState.status);
  if (indicator) {
    indicator.setAttribute("data-status", availabilityState.status);
  }
  if (toggleButton) {
    toggleButton.setAttribute("data-status", availabilityState.status);
  }
  if (toggleDot) {
    toggleDot.setAttribute("data-status", availabilityState.status);
  }
  if (labelNode) {
    labelNode.textContent = config.label;
  }
  if (toggleLabelNode) {
    toggleLabelNode.textContent = config.toggleLabel;
  }
}

function scheduleAvailabilityShift() {
  if (typeof window === "undefined") {
    return;
  }
  clearAvailabilityShiftTimer();
  const config = getAvailabilityConfig(availabilityState.status);
  let range = config.cycleRange || { min: 60000, max: 120000 };
  if (availabilityState.status === "available" && availabilityState.pendingShortCycle) {
    const hasRecentUserMessage =
      availabilityState.lastUserMessageAt &&
      Date.now() - availabilityState.lastUserMessageAt <= AVAILABILITY_SHORT_CYCLE_EXPIRY_MS;
    if (hasRecentUserMessage) {
      range = AVAILABILITY_SHORT_CYCLE_RANGE;
    }
    availabilityState.pendingShortCycle = false;
  }
  const wait = randomBetween(range.min || 60000, range.max || range.min || 120000);
  availabilityState.timerId = window.setTimeout(() => {
    availabilityState.timerId = null;
    const nextStatus = availabilityState.status === "available" ? "away" : "available";
    setAiAvailability(nextStatus);
  }, wait);
}

function handleAvailabilityToggleClick() {
  if (availabilityState.status === "available") {
    beginManualDowntimeWindow();
    return;
  }
  endManualDowntimeWindow();
}

function clearAvailabilityShiftTimer() {
  if (typeof window === "undefined") {
    availabilityState.timerId = null;
    return;
  }
  if (availabilityState.timerId) {
    window.clearTimeout(availabilityState.timerId);
    availabilityState.timerId = null;
  }
}

function clearReturnFromAwayTimer() {
  if (typeof window === "undefined") {
    availabilityState.returnFromAwayTimerId = null;
    return;
  }
  if (availabilityState.returnFromAwayTimerId) {
    window.clearTimeout(availabilityState.returnFromAwayTimerId);
    availabilityState.returnFromAwayTimerId = null;
  }
}

function scheduleReturnToAvailableAfterUserMessage() {
  if (typeof window === "undefined") {
    return;
  }
  clearReturnFromAwayTimer();
  const wait = randomBetween(
    AVAILABILITY_SHORT_CYCLE_RANGE.min,
    AVAILABILITY_SHORT_CYCLE_RANGE.max
  );
  availabilityState.returnFromAwayTimerId = window.setTimeout(() => {
    availabilityState.returnFromAwayTimerId = null;
    setAiAvailability("available");
  }, wait);
}

function beginManualDowntimeWindow() {
  if (typeof window === "undefined" || availabilityState.isManualDowntimeActive) {
    return;
  }
  availabilityState.isManualDowntimeActive = true;
  updateAiAvailabilityUi();
  captureActiveLouReplyForLater();
  setAiAvailability("away", { skipSchedule: true });
  const wait = randomBetween(MANUAL_AWAY_DURATION_MS.min, MANUAL_AWAY_DURATION_MS.max);
  if (availabilityState.manualDowntimeTimerId) {
    window.clearTimeout(availabilityState.manualDowntimeTimerId);
  }
  availabilityState.manualDowntimeTimerId = window.setTimeout(() => {
    availabilityState.manualDowntimeTimerId = null;
    availabilityState.isManualDowntimeActive = false;
    updateAiAvailabilityUi();
    setAiAvailability("available");
  }, wait);
}

function endManualDowntimeWindow() {
  if (typeof window !== "undefined" && availabilityState.manualDowntimeTimerId) {
    window.clearTimeout(availabilityState.manualDowntimeTimerId);
    availabilityState.manualDowntimeTimerId = null;
  }
  if (availabilityState.isManualDowntimeActive) {
    availabilityState.isManualDowntimeActive = false;
    updateAiAvailabilityUi();
  }
  setAiAvailability("available");
}

function captureActiveLouReplyForLater() {
  if (!louReplyState.referenceMessage || !louReplyState.serverId || !louReplyState.channelId) {
    return;
  }
  availabilityState.pendingLouReply = {
    serverId: louReplyState.serverId,
    channelId: louReplyState.channelId,
    referenceMessage: louReplyState.referenceMessage,
  };
  cancelLouReplyTimer();
  cancelLouReplyRequest();
  interruptLouOutput();
}

function dispatchPendingLouReply() {
  if (!availabilityState.pendingLouReply) {
    return;
  }
  const payload = availabilityState.pendingLouReply;
  availabilityState.pendingLouReply = null;
  scheduleLouReplyCountdown(payload);
}

function getAvailabilityCooldownDelay() {
  if (!availabilityState.cooldownUntil) {
    return 0;
  }
  return Math.max(0, availabilityState.cooldownUntil - Date.now());
}

function getAvailabilityResponseLag() {
  const config = getAvailabilityConfig(availabilityState.status);
  const range = config.responseLag;
  const baseLag = range ? randomBetween(range.min || 0, range.max || range.min || 0) : 0;
  return Math.max(0, baseLag + getAvailabilityCooldownDelay());
}

function getAvailabilityTypingLag() {
  const config = getAvailabilityConfig(availabilityState.status);
  const range = config.typingLag;
  if (!range) return 0;
  return Math.max(0, randomBetween(range.min || 0, range.max || range.min || 0));
}

function createLouOutputController() {
  return {
    cancelled: false,
    listeners: [],
    cancel() {
      if (this.cancelled) return;
      this.cancelled = true;
      this.listeners.forEach((listener) => listener());
      this.listeners = [];
    },
    onCancel(callback) {
      if (this.cancelled) {
        callback();
        return () => {};
      }
      this.listeners.push(callback);
      return () => {
        this.listeners = this.listeners.filter((listener) => listener !== callback);
      };
    },
  };
}

async function waitForController(ms, controller) {
  if (!controller) {
    await delay(ms);
    return true;
  }
  if (controller.cancelled) {
    return false;
  }
  return new Promise((resolve) => {
    const timeoutId = window.setTimeout(() => {
      cleanup();
      resolve(!controller.cancelled);
    }, Math.max(0, ms));
    const cancelHandler = () => {
      window.clearTimeout(timeoutId);
      cleanup();
      resolve(false);
    };
    const cleanup = controller.onCancel(cancelHandler);
  });
}

function createMessageNode(message, channelMessages) {
  const profile = profiles[message.authorId] ?? profiles.model ?? {
    name: "Desconhecido",
    initials: "??",
  };
  const row = document.createElement("article");
  row.className = "message-row";
  if (message.authorId === "user") row.classList.add("is-user");
  row.dataset.messageId = message.id;

  const avatar = buildAvatar(profile);
  const content = document.createElement("div");
  content.className = "message-content";

  const header = document.createElement("div");
  header.className = "message-header";
  const author = document.createElement("span");
  author.className = "message-author";
  author.textContent = profile.name;
  const timestamp = document.createElement("span");
  timestamp.className = "message-timestamp";
  timestamp.textContent = formatTime(message.timestamp);
  header.append(author, timestamp);

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  const safeHTML = escapeHTML(message.content).replace(/\n/g, "<br>");
  bubble.innerHTML = safeHTML;

  if (message.replyTo) {
    const reply = buildReplyPreview(message.replyTo, channelMessages);
    if (reply) bubble.prepend(reply);
  }

  if (Array.isArray(message.attachments) && message.attachments.length) {
    const attachmentsNode = document.createElement("div");
    attachmentsNode.className = "message-attachments";
    message.attachments.forEach((attachment) => {
      if (attachment.type === "gif" && attachment.url) {
        const figure = document.createElement("figure");
        figure.className = "message-attachment";
        const img = document.createElement("img");
        img.src = normalizeAssetPath(attachment.url);
        img.alt = attachment.name ? `GIF ${attachment.name}` : "GIF anexado";
        img.loading = "lazy";
        figure.appendChild(img);
        attachmentsNode.appendChild(figure);
      }
    });
    if (attachmentsNode.childNodes.length) {
      bubble.appendChild(attachmentsNode);
    }
  }

  const actions = document.createElement("div");
  actions.className = "message-actions";
  const replyButton = document.createElement("button");
  replyButton.type = "button";
  replyButton.className = "message-action";
  replyButton.dataset.messageAction = "reply";
  replyButton.title = "Responder";
  replyButton.setAttribute("aria-label", "Responder mensagem");
  replyButton.innerHTML = '<i class="fas fa-reply" aria-hidden="true"></i>';
  actions.appendChild(replyButton);

  content.append(header, bubble);
  row.append(avatar, content, actions);
  return row;
}

function buildAvatar(profile) {
  const wrapper = document.createElement("div");
  wrapper.className = "avatar";
  if (profile.avatar) {
    const img = document.createElement("img");
    img.alt = `Avatar de ${profile.name}`;
    img.src = normalizeAssetPath(profile.avatar);
    img.addEventListener("error", () => {
      img.remove();
      wrapper.textContent = profile.initials ?? profile.name.slice(0, 2).toUpperCase();
    });
    wrapper.appendChild(img);
  } else {
    wrapper.textContent = profile.initials ?? profile.name.slice(0, 2).toUpperCase();
  }
  return wrapper;
}

function buildReplyPreview(messageId, channelMessages) {
  const target = channelMessages.find((msg) => msg.id === messageId);
  if (!target) return null;
  const profile = profiles[target.authorId] ?? profiles.model ?? { name: "Desconhecido" };
  const preview = document.createElement("div");
  preview.className = "reply-preview";
  preview.textContent = `${profile.name}: ${target.content.slice(0, 70)}${
    target.content.length > 70 ? "…" : ""
  }`;
  return preview;
}

function formatDay(isoDate) {
  const date = new Date(isoDate);
  return date.toLocaleDateString("pt-BR", {
    weekday: "short",
    day: "2-digit",
    month: "short",
  });
}

function formatTime(isoDate) {
  const date = new Date(isoDate);
  return date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function hydrateUserCard() {
  if (!profiles.user) return;
  elements.userName.textContent = profiles.user.name;
  const avatar = buildAvatar(profiles.user);
  const nodes = Array.from(avatar.childNodes);
  elements.userAvatar.replaceChildren(...nodes);
}

function showEmptyState(title, text) {
  if (!elements.emptyState) return;
  elements.emptyState.querySelector(".empty-title").textContent = title;
  elements.emptyState.querySelector(".empty-text").textContent = text;
  elements.emptyState.classList.add("is-visible");
}

function hideEmptyState() {
  elements.emptyState?.classList.remove("is-visible");
}

async function handleFormSubmit(event) {
  event.preventDefault();
  const channel = getActiveChannel();
  if (!channel) return;
  const form = event.currentTarget || event.target;
  const textarea = form?.querySelector("textarea") || elements.messageInput;
  if (!textarea) return;
  const text = textarea.value.trim();
  if (!text) return;

  const server = getActiveServer();
  if (!server) return;
  const replyToId = replyState.message?.id ?? null;

  try {
    const newMessage = await postMessage({
      serverId: server.id,
      channelId: channel.id,
      authorId: "user",
      content: text,
      replyTo: replyToId,
    });

    channel.messages.push(newMessage);
    analyzeVoiceIntentsFromMessage(text, { serverId: server.id, channelId: channel.id });
    textarea.value = "";
    autoResizeTextarea(textarea);
    clearReplyTarget();
    registerUserActivity();
    renderMessages();
    queueLouReplyAfterUserMessage(server.id, channel.id, newMessage);
  } catch (error) {
    console.error("Falha ao enviar mensagem", error);
  }
}

async function triggerLouReplyFlow(serverId, channelId, referenceMessage, options = {}) {
  const { token } = options;
  const requestStartedAt = Date.now();
  const targetInitialDelay =
    randomBetween(LOU_TYPING_INITIAL_DELAY.min, LOU_TYPING_INITIAL_DELAY.max) + getAvailabilityTypingLag();
  const abortController = new AbortController();
  louReplyState.abortController = abortController;
  let payload;
  try {
    payload = await postJSON(
      `${API_BASE}/ai/reply`,
      {
        serverId,
        channelId,
        replyTo: referenceMessage?.id ?? null,
      },
      { signal: abortController.signal }
    );
  } catch (error) {
    if (abortController.signal.aborted) {
      return;
    }
    console.error("Falha ao gerar resposta da Lou", error);
    const channel = findChannel(serverId, channelId);
    if (!channel) return;
    const friendlyMessage = getFriendlyAiErrorMessage(error);
    channel.messages.push({
      id: `ai-error-${Date.now()}`,
      role: "model",
      authorId: "model",
      content: friendlyMessage,
      parts: [friendlyMessage],
      timestamp: new Date().toISOString(),
      isError: true,
    });
    if (serverId === state.activeServerId && channelId === state.activeChannelId) {
      renderMessages();
    }
    return;
  } finally {
    if (louReplyState.abortController === abortController) {
      louReplyState.abortController = null;
    }
  }
  if (token && token !== louReplyState.generationToken) {
    return;
  }
  const newMessages = Array.isArray(payload?.messages) ? payload.messages : [];
  if (!newMessages.length) {
    return;
  }
  const elapsed = Date.now() - requestStartedAt;
  const remainingInitialWait = Math.max(targetInitialDelay - elapsed, 0);
  const outputController = createLouOutputController();
  louReplyState.outputController = outputController;
  await playLouTypingSequence(serverId, channelId, newMessages, {
    initialWait: remainingInitialWait,
    controller: outputController,
  });
  if (louReplyState.outputController === outputController) {
    louReplyState.outputController = null;
  }
  if (outputController.cancelled) {
    return;
  }
  proactiveState.lastUserActivity = Date.now();
  startProactiveTimer();
  if (payload?.reasoning) {
    console.info("Raciocínio da Lou:", payload.reasoning);
  }
}

function insertLouTypingIndicator(serverId, channelId) {
  const channel = findChannel(serverId, channelId);
  if (!channel) return null;
  const placeholder = {
    id: `temp-lou-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`,
    role: "model",
    authorId: "model",
    content: "digitando…",
    parts: ["digitando…"],
    timestamp: new Date().toISOString(),
    isTyping: true,
  };
  channel.messages.push(placeholder);
  if (serverId === state.activeServerId && channelId === state.activeChannelId) {
    renderMessages();
  }
  return placeholder;
}

function removeLouTypingIndicator(serverId, channelId, messageId) {
  const channel = findChannel(serverId, channelId);
  if (!channel) return false;
  const index = channel.messages.findIndex((msg) => msg.id === messageId);
  if (index === -1) return false;
  channel.messages.splice(index, 1);
  return true;
}

async function playLouTypingSequence(serverId, channelId, messages, options = {}) {
  if (!Array.isArray(messages) || messages.length === 0) return;
  const channel = findChannel(serverId, channelId);
  if (!channel) return;
  const controller = options.controller;
  const initialWait = Math.max(0, Number(options.initialWait) || 0);
  if (!(await waitForController(initialWait, controller))) {
    return;
  }
  if (controller?.cancelled) return;
  let placeholder = insertLouTypingIndicator(serverId, channelId);
  let detachPlaceholderCancel = null;
  if (controller) {
    detachPlaceholderCancel = controller.onCancel(() => {
      if (placeholder) {
        removeLouTypingIndicator(serverId, channelId, placeholder.id);
        placeholder = null;
      }
    });
  }
  const removePlaceholder = () => {
    if (placeholder) {
      removeLouTypingIndicator(serverId, channelId, placeholder.id);
      placeholder = null;
    }
    if (typeof detachPlaceholderCancel === "function") {
      detachPlaceholderCancel();
      detachPlaceholderCancel = null;
    }
  };
  for (let index = 0; index < messages.length; index += 1) {
    const typingDuration = randomBetween(LOU_TYPING_BURST_DELAY.min, LOU_TYPING_BURST_DELAY.max);
    if (!(await waitForController(typingDuration, controller))) {
      removePlaceholder();
      return;
    }
    removePlaceholder();
    if (controller?.cancelled) {
      return;
    }
    channel.messages.push(messages[index]);
    if (serverId === state.activeServerId && channelId === state.activeChannelId) {
      renderMessages();
    }
    if (index < messages.length - 1) {
      const pause = randomBetween(LOU_TYPING_BETWEEN_DELAY.min, LOU_TYPING_BETWEEN_DELAY.max);
      if (!(await waitForController(pause, controller))) {
        return;
      }
      if (controller?.cancelled) {
        return;
      }
      placeholder = insertLouTypingIndicator(serverId, channelId);
      if (controller) {
        detachPlaceholderCancel = controller.onCancel(() => {
          if (placeholder) {
            removeLouTypingIndicator(serverId, channelId, placeholder.id);
            placeholder = null;
          }
        });
      }
    }
  }
  removePlaceholder();
  flushVoiceIntentQueue(serverId, channelId);
}

function getFriendlyAiErrorMessage(error) {
  const raw = String(error?.message || error || "");
  if (raw.includes("GEMINI_API_KEY")) {
    return "Configure a variável GEMINI_API_KEY no backend para ativar as respostas da Lou.";
  }
  if (raw.includes("503")) {
    return "O backend recusou o pedido agora pouco. Tente novamente em instantes.";
  }
  return "Não consegui responder agora. Tente de novo em instantes.";
}

function findChannel(serverId, channelId) {
  const server = state.servers.find((srv) => srv.id === serverId);
  if (!server) return null;
  return server.channels.find((chn) => chn.id === channelId) ?? null;
}

function normalizeAssetPath(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  const trimmed = path.replace(/^\/+/, "");
  return `/${trimmed}`;
}

async function postMessage({ serverId, channelId, authorId, content, replyTo, attachments }) {
  return postJSON(`${API_BASE}/servers/${serverId}/channels/${channelId}/messages`, {
    authorId,
    content,
    replyTo,
    attachments,
  });
}

function autoResizeTextarea(target = elements.messageInput) {
  const textarea = target;
  if (!textarea) return;
  if (!textarea.dataset.baseHeight) {
    textarea.dataset.baseHeight = String(textarea.clientHeight || 46);
  }
  const baseHeight = Number(textarea.dataset.baseHeight) || 46;
  const maxHeight = 120;
  textarea.style.height = "auto";
  const nextHeight = Math.min(Math.max(textarea.scrollHeight, baseHeight), maxHeight);
  textarea.style.height = `${nextHeight}px`;
  if (textarea.scrollHeight > maxHeight || nextHeight >= maxHeight) {
    textarea.classList.add("is-scrollable");
  } else {
    textarea.classList.remove("is-scrollable");
  }
}

function bindEvents() {
  elements.messageForm?.addEventListener("submit", handleFormSubmit);
  elements.messageInput?.addEventListener("input", (event) => autoResizeTextarea(event.target));
  elements.messageInput?.addEventListener("keydown", handleComposerKeyDown);
  elements.channelCreateButton?.addEventListener("click", handleCreateChannelFlow);
  elements.channelList?.addEventListener("click", handleChannelListClick);
  elements.channelList?.addEventListener("keydown", handleChannelListKeyDown);
  elements.voiceChannelList?.addEventListener("click", handleVoiceChannelListClick);
  elements.messageList?.addEventListener("click", handleMessageListClick);
  elements.serverSettingsButton?.addEventListener("click", () => {
    const server = getActiveServer();
    if (!server) return;
    openServerSettingsDialog(server);
  });
  elements.voiceLeave?.addEventListener("click", () => leaveVoiceChannel());
  elements.voiceShareStop?.addEventListener("click", handleVoiceShareStopClick);
  elements.voiceShareTrigger?.addEventListener("click", handleVoiceShareTriggerClick);
  elements.voiceShareFileInput?.addEventListener("change", handleVoiceShareFileChange);
  elements.voiceShareToggle?.addEventListener("click", handleVoiceShareToggleClick);
  elements.voiceShareCollapseBanner?.addEventListener(
    "click",
    handleVoiceShareCollapseBannerClick
  );
  elements.profileSettingsButton?.addEventListener("click", () => {
    openProfileSettingsDialog();
  });
  elements.replyCancel?.addEventListener("click", clearReplyTarget);
  elements.personalityButton?.addEventListener("click", () => {
    openPersonalityEditor();
  });
  elements.personalityCancel?.addEventListener("click", closePersonalityEditor);
  elements.personalityClose?.addEventListener("click", closePersonalityEditor);
  elements.personalityPanel?.addEventListener("click", (event) => event.stopPropagation());
  elements.personalityOverlay?.addEventListener("click", (event) => {
    if (event.target === elements.personalityOverlay) {
      closePersonalityEditor();
    }
  });
  elements.personalityCategoryList?.addEventListener("click", handlePersonalityCategoryClick);
  elements.personalitySave?.addEventListener("click", handlePersonalitySave);
  elements.contextToggle?.addEventListener("click", openContextPanel);
  elements.contextClose?.addEventListener("click", closeContextPanel);
  elements.contextOverlay?.addEventListener("click", (event) => {
    if (event.target === elements.contextOverlay) {
      closeContextPanel();
    }
  });
  elements.contextPanel?.addEventListener("click", (event) => event.stopPropagation());
  elements.availabilityToggle?.addEventListener("click", handleAvailabilityToggleClick);
  elements.proactiveTrigger?.addEventListener("click", () => triggerProactiveMessage({ manual: true }));
  elements.gifButton?.addEventListener("click", openGifPicker);
  elements.gifClose?.addEventListener("click", closeGifPicker);
  elements.gifUpload?.addEventListener("click", handleGifUploadClick);
  elements.gifFileInput?.addEventListener("change", handleGifFileChange);
  elements.gifOverlay?.addEventListener("click", (event) => {
    if (event.target === elements.gifOverlay) {
      closeGifPicker();
    }
  });
  elements.gifPanel?.addEventListener("click", (event) => event.stopPropagation());
  elements.gifSearch?.addEventListener("input", handleGifSearchInput);
  elements.gifList?.addEventListener("click", handleGifListClick);
  document.addEventListener("keydown", handleGifEscapeKey);
  setupVoicePlaybackUnlockListeners();
  window.addEventListener("resize", () => scheduleChannelLimitCheck(getActiveServer()));
}

function handleComposerKeyDown(event) {
  if (event.key !== "Enter" || event.shiftKey) return;
  const form = event.target?.closest("form");
  if (!form) return;
  event.preventDefault();
  form.requestSubmit();
}

async function init() {
  bindEvents();
  initAiAvailability();
  autoResizeTextarea(elements.messageInput);
  updateVoiceShareVisibilityUi();
  try {
    const response = await fetch(`${API_BASE}/bootstrap`);
    if (!response.ok) throw new Error("Falha ao carregar dados iniciais");
    const payload = await response.json();
    profiles = payload.profiles ?? {};
    state.servers = payload.servers ?? [];
    state.activeServerId = state.servers[0]?.id ?? null;
    state.activeChannelId = state.servers[0]?.channels[0]?.id ?? null;
  } catch (error) {
    console.error("Bootstrap falhou", error);
  } finally {
    state.isLoading = false;
    hydrateUserCard();
    renderServers();
    renderChannels();
    renderChatArea();
    refreshProactiveWatcher({ resetAttempts: true });
  }
}

init();

function handleChannelListClick(event) {
  const actionButton = event.target.closest("[data-channel-action]");
  const channelButton = event.target.closest(".channel-button");
  const server = getActiveServer();
  if (!server) return;
  if (actionButton) {
    event.preventDefault();
    event.stopPropagation();
    const container = actionButton.closest(".channel-button");
    if (!container) return;
    const channel = server.channels.find((chn) => chn.id === container.dataset.channelId);
    if (!channel) return;
    if (actionButton.dataset.channelAction === "rename") {
      openChannelRenameDialog(server, channel);
    } else if (actionButton.dataset.channelAction === "delete") {
      openChannelDeleteDialog(server, channel);
    }
    return;
  }
  if (channelButton && channelButton.dataset.channelId) {
    const channelId = channelButton.dataset.channelId;
    if (state.activeChannelId === channelId) return;
    state.activeChannelId = channelId;
    renderChannels();
    renderChatArea();
    refreshProactiveWatcher();
  }
}

function handleChannelListKeyDown(event) {
  if (!(event.key === "Enter" || event.key === " ")) return;
  const actionButton = event.target.closest("[data-channel-action]");
  if (!actionButton) return;
  event.preventDefault();
  actionButton.click();
}

function handleMessageListClick(event) {
  const actionButton = event.target.closest("[data-message-action]");
  if (!actionButton) return;
  event.preventDefault();
  const messageRow = actionButton.closest(".message-row");
  if (!messageRow) return;
  const channel = getActiveChannel();
  const server = getActiveServer();
  if (!channel || !server) return;
  const message = channel.messages.find((msg) => msg.id === messageRow.dataset.messageId);
  if (!message) return;
  setReplyTarget(server.id, channel.id, message);
}

function setReplyTarget(serverId, channelId, message) {
  replyState.serverId = serverId;
  replyState.channelId = channelId;
  replyState.message = message;
  updateReplyIndicator();
  elements.messageInput?.focus();
}

function clearReplyTarget() {
  if (!replyState.message) {
    updateReplyIndicator();
    return;
  }
  replyState.serverId = null;
  replyState.channelId = null;
  replyState.message = null;
  updateReplyIndicator();
}

function updateReplyIndicator() {
  if (!elements.replyIndicator || !elements.replyAuthor || !elements.replySnippet) return;
  if (!replyState.message) {
    elements.replyIndicator.classList.add("is-hidden");
    return;
  }
  const profile = profiles[replyState.message.authorId] ?? profiles.model ?? { name: "Desconhecido" };
  const rawSnippet = replyState.message.content ?? replyState.message.parts?.[0] ?? "";
  const cleanSnippet = rawSnippet.trim().replace(/\s+/g, " ");
  const truncated = cleanSnippet.length > 90 ? `${cleanSnippet.slice(0, 90)}…` : cleanSnippet;
  elements.replyAuthor.textContent = profile.name;
  elements.replySnippet.textContent = truncated;
  elements.replyIndicator.classList.remove("is-hidden");
}

async function handleCreateChannelFlow() {
  const server = getActiveServer();
  if (!server) return;
  if (Array.isArray(server.channels) && server.channels.length >= MAX_TEXT_CHANNELS) {
    window.alert(`Limite de ${MAX_TEXT_CHANNELS} chats atingido. Exclua um canal antes de criar outro.`);
    updateChannelCreationAvailability(server);
    return;
  }
  const name = generateAutoChannelName(server);
  try {
    const channel = await postJSON(`${API_BASE}/servers/${server.id}/channels`, { name });
    server.channels.push(channel);
    state.activeChannelId = channel.id;
    renderChannels();
    renderChatArea();
    refreshProactiveWatcher({ resetAttempts: true });
  } catch (error) {
    console.error("Falha ao criar canal", error);
  }
}

function generateAutoChannelName(server) {
  const baseName = "Novo Chat";
  if (!server || !Array.isArray(server.channels) || server.channels.length === 0) {
    return baseName;
  }
  const pattern = /^novo chat(?:\s+(\d+))?$/i;
  let nextIndex = 1;
  for (const channel of server.channels) {
    const match = typeof channel.name === "string" ? channel.name.match(pattern) : null;
    if (!match) continue;
    const number = match[1] ? Number.parseInt(match[1], 10) : 1;
    if (Number.isFinite(number) && number >= nextIndex) {
      nextIndex = number + 1;
    }
  }
  return nextIndex === 1 ? baseName : `${baseName} ${nextIndex}`;
}

function openChannelRenameDialog(server, channel) {
  const safeName = escapeHTML(channel.name);
  const template = `
    <div class="lou-dialog" role="dialog" aria-modal="true">
      <div class="lou-dialog__header">
        <div>
          <h2 class="lou-dialog__title">Renomear canal</h2>
          <p class="lou-dialog__subtitle">@${safeName}</p>
        </div>
        <button class="lou-dialog__close" type="button" data-action="close">×</button>
      </div>
      <form class="lou-form" data-role="channel-form">
        <label class="lou-field lou-field--spaced">
          <span class="lou-label">Nome do canal</span>
          <input class="lou-input" name="name" value="${safeName}" maxlength="48" autocomplete="off" />
        </label>
        <div class="lou-dialog__actions">
          <button class="lou-button" type="button" data-action="cancel">Cancelar</button>
          <button class="lou-button primary" type="submit">Salvar</button>
        </div>
      </form>
    </div>`;
  const backdrop = openDialog(template);
  if (!backdrop) return;
  const dialog = backdrop.querySelector(".lou-dialog");
  const form = dialog.querySelector("[data-role=channel-form]");
  const nameInput = form.querySelector('input[name="name"]');
  const cancelButtons = dialog.querySelectorAll('[data-action="close"],[data-action="cancel"]');
  cancelButtons.forEach((btn) => btn.addEventListener("click", closeDialog));
  nameInput.focus();
  nameInput.select();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const newName = nameInput.value.trim();
    if (!newName) {
      nameInput.focus();
      return;
    }
    try {
      const updated = await patchJSON(`${API_BASE}/servers/${server.id}/channels/${channel.id}`, { name: newName });
      Object.assign(channel, updated);
      renderChannels();
      renderChatArea();
      closeDialog();
    } catch (error) {
      console.error("Falha ao renomear canal", error);
      window.alert(error.message);
    }
  });
}

function openChannelDeleteDialog(server, channel) {
  const safeName = escapeHTML(channel.name);
  const template = `
    <div class="lou-dialog" role="dialog" aria-modal="true">
      <div class="lou-dialog__header">
        <div>
          <h2 class="lou-dialog__title">Excluir canal</h2>
          <p class="lou-dialog__subtitle">@${safeName}</p>
        </div>
        <button class="lou-dialog__close" type="button" data-action="close">×</button>
      </div>
      <p>Essa ação removerá todo o histórico de mensagens do canal. Tem certeza?</p>
      <div class="lou-dialog__actions">
        <button class="lou-button" type="button" data-action="cancel">Cancelar</button>
        <button class="lou-button danger" type="button" data-action="confirm">Excluir</button>
      </div>
    </div>`;
  const backdrop = openDialog(template);
  if (!backdrop) return;
  const dialog = backdrop.querySelector(".lou-dialog");
  const cancelButtons = dialog.querySelectorAll('[data-action="close"],[data-action="cancel"]');
  cancelButtons.forEach((btn) => btn.addEventListener("click", closeDialog));
  const confirmButton = dialog.querySelector('[data-action="confirm"]');
  confirmButton.addEventListener("click", async () => {
    confirmButton.disabled = true;
    try {
      await deleteJSON(`${API_BASE}/servers/${server.id}/channels/${channel.id}`);
      removeChannelFromState(server.id, channel.id);
      renderChannels();
      renderChatArea();
      closeDialog();
    } catch (error) {
      console.error("Falha ao excluir canal", error);
      window.alert(error.message);
      confirmButton.disabled = false;
    }
  });
}

function removeChannelFromState(serverId, channelId) {
  const targetServer = state.servers.find((srv) => srv.id === serverId);
  if (!targetServer) return;
  targetServer.channels = targetServer.channels.filter((chn) => chn.id !== channelId);
  if (state.activeChannelId === channelId) {
    state.activeChannelId = targetServer.channels[0]?.id ?? null;
  }
  if (replyState.channelId === channelId) {
    clearReplyTarget();
  }
  refreshProactiveWatcher({ resetAttempts: true });
}

function openServerSettingsDialog(server) {
  const serverName = server.name ?? "Servidor";
  const safeName = escapeHTML(serverName);
  const template = `
    <div class="lou-dialog" role="dialog" aria-modal="true">
      <div class="lou-dialog__header">
        <div>
          <h2 class="lou-dialog__title">Configurações do servidor</h2>
          <p class="lou-dialog__subtitle">${safeName}</p>
        </div>
        <button class="lou-dialog__close" type="button" data-action="close">×</button>
      </div>
      <form class="lou-form" data-role="server-form">
        <label class="lou-field lou-field--spaced">
          <span class="lou-label">Nome do servidor</span>
          <input class="lou-input" name="name" value="${safeName}" maxlength="48" autocomplete="off" />
        </label>
        <div class="lou-dialog__actions">
          <button class="lou-button danger" type="button" data-action="delete">Excluir</button>
          <span style="flex: 1"></span>
          <button class="lou-button" type="button" data-action="cancel">Cancelar</button>
          <button class="lou-button primary" type="submit">Salvar</button>
        </div>
      </form>
    </div>`;
  const backdrop = openDialog(template);
  if (!backdrop) return;
  const dialog = backdrop.querySelector(".lou-dialog");
  const form = dialog.querySelector("[data-role=server-form]");
  const nameInput = form.querySelector('input[name="name"]');
  const deleteButton = form.querySelector('[data-action="delete"]');
  const cancelButtons = dialog.querySelectorAll('[data-action="close"],[data-action="cancel"]');
  cancelButtons.forEach((btn) => btn.addEventListener("click", closeDialog));
  nameInput.focus();
  nameInput.select();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const newName = nameInput.value.trim();
    if (!newName) {
      nameInput.focus();
      return;
    }
    const payload = { name: newName };
    try {
      const updated = await patchJSON(`${API_BASE}/servers/${server.id}`, payload);
      Object.assign(server, updated);
      renderServers();
      renderChannels();
      renderChatArea();
      closeDialog();
    } catch (error) {
      console.error("Falha ao atualizar servidor", error);
      window.alert(error.message);
    }
  });

  let deleteConfirmTimer = null;
  deleteButton.addEventListener("click", async () => {
    if (!deleteButton.dataset.confirmed) {
      deleteButton.dataset.confirmed = "true";
      const originalLabel = "Excluir";
      deleteButton.textContent = "Confirmar exclusão";
      deleteConfirmTimer = window.setTimeout(() => {
        deleteButton.dataset.confirmed = "";
        deleteButton.textContent = originalLabel;
      }, 3500);
      return;
    }
    window.clearTimeout(deleteConfirmTimer);
    deleteButton.disabled = true;
    try {
      await deleteJSON(`${API_BASE}/servers/${server.id}`);
      const wasActive = state.activeServerId === server.id;
      state.servers = state.servers.filter((item) => item.id !== server.id);
      if (replyState.serverId === server.id) {
        clearReplyTarget();
      }
      if (!state.servers.length) {
        state.activeServerId = null;
        state.activeChannelId = null;
      } else if (wasActive) {
        state.activeServerId = state.servers[0].id;
        state.activeChannelId = state.servers[0].channels[0]?.id ?? null;
      }
      renderServers();
      renderChannels();
      renderChatArea();
      refreshProactiveWatcher({ resetAttempts: true });
      closeDialog();
    } catch (error) {
      console.error("Falha ao excluir servidor", error);
      window.alert(error.message);
      deleteButton.disabled = false;
    }
  });
}

function openProfileSettingsDialog() {
  if (!profiles.user && !profiles.model) return;
  let currentKey = "user";
  let currentAvatarValue = "";
  const template = `
    <div class="lou-dialog" role="dialog" aria-modal="true">
      <div class="lou-dialog__header">
        <div>
          <h2 class="lou-dialog__title">Perfis</h2>
          <p class="lou-dialog__subtitle">Configure nome e avatar</p>
        </div>
        <button class="lou-dialog__close" type="button" data-action="close">×</button>
      </div>
      <div class="lou-tab-group" data-role="profile-tabs">
        <button class="lou-tab is-active" type="button" data-profile-key="user">Você</button>
        <button class="lou-tab" type="button" data-profile-key="model">Lou</button>
      </div>
      <div class="lou-profile-preview">
        <div class="lou-avatar-preview" data-role="avatar-preview"></div>
        <div class="lou-avatar-actions">
          <p class="lou-hint">Envie PNG/JPG (até 2 MB).</p>
          <button class="ghost-button" type="button" data-action="upload-avatar">Enviar imagem</button>
          <input type="file" data-role="profile-avatar-file" accept="image/png,image/jpeg,image/webp,image/gif" hidden />
          <p class="lou-hint" data-role="avatar-status"></p>
        </div>
      </div>
      <form class="lou-form" data-role="profile-form">
        <label class="lou-field lou-field--spaced">
          <span class="lou-label">Nome</span>
          <input class="lou-input" name="name" maxlength="48" autocomplete="off" />
        </label>
        <div class="lou-dialog__actions">
          <button class="lou-button" type="button" data-action="cancel">Cancelar</button>
          <button class="lou-button primary" type="submit">Salvar</button>
        </div>
      </form>
    </div>`;
  const backdrop = openDialog(template);
  if (!backdrop) return;
  const dialog = backdrop.querySelector(".lou-dialog");
  const subtitle = dialog.querySelector(".lou-dialog__subtitle");
  const tabs = dialog.querySelectorAll("[data-profile-key]");
  const form = dialog.querySelector("[data-role=profile-form]");
  const nameInput = form.querySelector('input[name="name"]');
  const preview = dialog.querySelector("[data-role=avatar-preview]");
  const avatarUploadButton = dialog.querySelector('[data-action="upload-avatar"]');
  const avatarFileInput = dialog.querySelector('[data-role="profile-avatar-file"]');
  const avatarStatus = dialog.querySelector('[data-role="avatar-status"]');
  const cancelButtons = dialog.querySelectorAll('[data-action="close"],[data-action="cancel"]');
  cancelButtons.forEach((btn) => btn.addEventListener("click", closeDialog));

  const updateAvatarPreview = (path) => {
    preview.innerHTML = "";
    const img = document.createElement("img");
    img.alt = "Prévia do avatar";
    const safePath = path && path.trim() ? path.trim() : "assets/avatars/default.png";
    img.src = normalizeAssetPath(safePath);
    img.addEventListener("error", () => {
      img.src = normalizeAssetPath("assets/avatars/default.png");
    });
    preview.appendChild(img);
  };

  const syncTabs = () => {
    tabs.forEach((tab) => {
      tab.classList.toggle("is-active", tab.dataset.profileKey === currentKey);
    });
    const profile = profiles[currentKey] ?? {};
    subtitle.textContent = currentKey === "user" ? "Seu perfil" : "Perfil da Lou";
    nameInput.value = profile.name ?? "";
    currentAvatarValue = profile.avatar ?? "";
    updateAvatarPreview(currentAvatarValue);
    if (avatarStatus) avatarStatus.textContent = "";
  };

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      currentKey = tab.dataset.profileKey;
      syncTabs();
    });
  });

  initializeAvatarUploadControls({
    uploadButton: avatarUploadButton,
    fileInput: avatarFileInput,
    statusNode: avatarStatus,
    onSuccess: (payload) => {
      const normalized = normalizeUploadedAvatarPath(payload);
      currentAvatarValue = normalized;
      updateAvatarPreview(normalized);
    },
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const newName = nameInput.value.trim();
    if (!newName) {
      nameInput.focus();
      return;
    }
    const normalizedAvatar = (currentAvatarValue ?? "").trim();
    const payload = {
      name: newName,
      avatar: normalizedAvatar || null,
    };
    try {
      const updated = await patchJSON(`${API_BASE}/profiles/${currentKey}`, payload);
      profiles[currentKey] = { ...(profiles[currentKey] ?? {}), ...updated };
      hydrateUserCard();
      renderMessages();
      closeDialog();
    } catch (error) {
      console.error("Falha ao atualizar perfil", error);
      window.alert(error.message);
    }
  });

  syncTabs();
  nameInput.focus();
  nameInput.select();
}

async function openPersonalityEditor() {
  if (!elements.personalityOverlay) return;
  elements.personalityOverlay.classList.remove("is-hidden");
  syncOverlayPresence();
  if (!personalityState.data) {
    await loadPersonalityData();
    return;
  }
  buildPersonalityDraft(true);
  renderPersonalityPanel();
}

function closePersonalityEditor() {
  elements.personalityOverlay?.classList.add("is-hidden");
  syncOverlayPresence();
}

async function loadPersonalityData(force = false) {
  if (personalityState.isLoading) return;
  if (personalityState.data && !force) {
    buildPersonalityDraft(true);
    renderPersonalityPanel();
    return;
  }
  personalityState.isLoading = true;
  setPersonalityStatus("Carregando ficha de personalidade…");
  try {
    const response = await fetch(`${API_BASE}/personality`);
    if (!response.ok) throw new Error("Falha ao carregar personalidade");
    const payload = await response.json();
    personalityState.data = payload ?? {};
    buildPersonalityDraft();
    renderPersonalityPanel();
  setPersonalityStatus("");
  } catch (error) {
    console.error("Falha ao carregar personalidade", error);
    setPersonalityStatus("Erro ao carregar personalidade");
  } finally {
    personalityState.isLoading = false;
    updatePersonalitySaveState({ skipStatus: true });
  }
}

function buildPersonalityDraft(preserveCategory = false) {
  const definition = personalityState.data?.personality_definition ?? {};
  personalityState.draft = JSON.parse(JSON.stringify(definition));
  const categoryKeys = Object.keys(definition);
  if (
    preserveCategory &&
    personalityState.activeCategory &&
    Object.prototype.hasOwnProperty.call(definition, personalityState.activeCategory)
  ) {
    // Keep current selection.
  } else {
    personalityState.activeCategory = categoryKeys[0] ?? null;
  }
  personalityState.hasUnsavedChanges = false;
}

function renderPersonalityPanel() {
  renderPersonalityCategories();
  if (personalityState.activeCategory) {
    renderPersonalityFields(personalityState.activeCategory);
  } else if (elements.personalityFields && elements.personalityEmpty) {
    elements.personalityFields.innerHTML = "";
    elements.personalityEmpty.textContent = "Nenhuma seção disponível.";
    elements.personalityEmpty.classList.remove("is-hidden");
  }
  updatePersonalitySaveState();
}

function renderPersonalityCategories() {
  if (!elements.personalityCategoryList) return;
  const target = elements.personalityCategoryList;
  target.innerHTML = "";
  const definition = personalityState.draft ?? {};
  const categoryKeys = Object.keys(definition);
  if (!categoryKeys.length) {
    const emptyNode = document.createElement("p");
    emptyNode.className = "personality-sidebar-empty";
    emptyNode.textContent = "O arquivo personality_prompt.json não possui seções para editar.";
    target.appendChild(emptyNode);
    return;
  }
  categoryKeys.forEach((key) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "personality-category";
    if (key === personalityState.activeCategory) button.classList.add("is-active");
    button.dataset.categoryKey = key;
    button.textContent = formatPersonalityLabel(key);
    target.appendChild(button);
  });
}

function handlePersonalityCategoryClick(event) {
  const button = event.target.closest("[data-category-key]");
  if (!button) return;
  const { categoryKey } = button.dataset;
  if (!categoryKey || categoryKey === personalityState.activeCategory) return;
  if (!personalityState.draft || !personalityState.draft[categoryKey]) return;
  personalityState.activeCategory = categoryKey;
  renderPersonalityPanel();
}

function renderPersonalityFields(categoryKey) {
  if (!elements.personalityFields || !elements.personalityEmpty) return;
  const definition = personalityState.draft ?? {};
  const fields = definition[categoryKey];
  elements.personalityFields.innerHTML = "";
  if (!fields) {
    elements.personalityEmpty.textContent = "Nada para editar nesta seção.";
    elements.personalityEmpty.classList.remove("is-hidden");
    return;
  }
  elements.personalityEmpty.classList.add("is-hidden");
  Object.entries(fields).forEach(([fieldKey, value]) => {
    const wrapper = document.createElement("label");
    wrapper.className = "personality-field";
    const label = document.createElement("span");
    label.className = "personality-field-label";
    label.textContent = formatPersonalityLabel(fieldKey);
    const input = buildPersonalityFieldInput(fieldKey, value, `${categoryKey}.${fieldKey}`);
    wrapper.append(label, input);
    elements.personalityFields.appendChild(wrapper);
  });
}

function buildPersonalityFieldInput(fieldKey, value, path) {
  const kind = determinePersonalityFieldKind(fieldKey, value);
  const isTextarea = kind === "list" || kind === "long";
  const input = document.createElement(isTextarea ? "textarea" : "input");
  if (!isTextarea) {
    if (kind === "int" || kind === "float") {
      input.type = "number";
      if (kind === "float") input.step = "0.01";
    } else {
      input.type = "text";
    }
  } else {
    input.rows = kind === "list" ? 4 : 3;
  }
  input.value = formatPersonalityFieldValue(kind, value);
  input.dataset.fieldPath = path;
  input.dataset.fieldType = kind;
  input.addEventListener("input", handlePersonalityFieldChange);
  if (kind === "list") {
    input.placeholder = "Separe os itens com quebras de linha";
  }
  return input;
}

function determinePersonalityFieldKind(fieldKey, value) {
  if (Array.isArray(value)) return "list";
  if (typeof value === "number") return Number.isInteger(value) ? "int" : "float";
  if (fieldKey === "DataNascimento") return "date";
  if (typeof value === "string" && (value.length > 120 || value.includes("\n"))) return "long";
  return "string";
}

function formatPersonalityFieldValue(kind, value) {
  if (value === null || value === undefined) return "";
  if (kind === "list" && Array.isArray(value)) {
    return value.join("\n");
  }
  if (kind === "date") {
    return formatDateForDisplay(String(value));
  }
  return String(value);
}

function handlePersonalityFieldChange(event) {
  const input = event.target;
  if (!(input instanceof HTMLInputElement || input instanceof HTMLTextAreaElement)) return;
  const path = input.dataset.fieldPath;
  if (!path) return;
  const kind = input.dataset.fieldType ?? "string";
  const parsedValue = parsePersonalityFieldValue(input.value, kind);
  setDraftValue(path, parsedValue);
  personalityState.hasUnsavedChanges = true;
  updatePersonalitySaveState();
}

function setDraftValue(path, value) {
  if (!personalityState.draft) return;
  const segments = path.split(".");
  const finalKey = segments.pop();
  if (!finalKey) return;
  let cursor = personalityState.draft;
  segments.forEach((segment) => {
    if (!Object.prototype.hasOwnProperty.call(cursor, segment)) {
      cursor[segment] = {};
    }
    cursor = cursor[segment];
  });
  cursor[finalKey] = value;
}

function parsePersonalityFieldValue(rawValue, kind) {
  const trimmed = rawValue.trim();
  switch (kind) {
    case "list": {
      const tokens = rawValue.split(/\r?\n|,/);
      return tokens.map((item) => item.trim()).filter(Boolean);
    }
    case "int": {
      if (!trimmed) return null;
      const parsed = Number.parseInt(trimmed, 10);
      return Number.isNaN(parsed) ? null : parsed;
    }
    case "float": {
      if (!trimmed) return null;
      const parsed = Number.parseFloat(trimmed);
      return Number.isNaN(parsed) ? null : parsed;
    }
    case "date": {
      if (!trimmed) return "";
      return normalizeDateForSave(trimmed);
    }
    default:
      return rawValue;
  }
}

function formatPersonalityLabel(key) {
  if (!key) return "";
  if (Object.prototype.hasOwnProperty.call(PERSONALITY_LABEL_OVERRIDES, key)) {
    return PERSONALITY_LABEL_OVERRIDES[key];
  }
  const spaced = key.replace(/([A-Z])/g, " $1").replace(/_/g, " ").trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function formatDateForDisplay(value) {
  const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) {
    const [, year, month, day] = isoMatch;
    return `${day}/${month}/${year}`;
  }
  return value;
}

function normalizeDateForSave(value) {
  const normalized = value.replace(/-/g, "/");
  const parts = normalized.split(/[\/]/);
  if (parts.length === 3 && parts[0].length === 2) {
    const [day, month, year] = parts;
    return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
  }
  return value;
}

function setPersonalityStatus(message) {
  if (!elements.personalityStatus) return;
  elements.personalityStatus.textContent = message ?? "";
}

function updatePersonalitySaveState(options = {}) {
  if (elements.personalitySave) {
    elements.personalitySave.disabled =
      !personalityState.hasUnsavedChanges || personalityState.isSaving || !personalityState.draft;
    elements.personalitySave.textContent = personalityState.isSaving ? "Salvando..." : "Salvar alterações";
  }
  if (!options.skipStatus && !personalityState.isSaving && !personalityState.isLoading) {
    if (personalityState.hasUnsavedChanges) {
      setPersonalityStatus("Alterações não salvas");
    } else {
      setPersonalityStatus("");
    }
  }
}

async function handlePersonalitySave() {
  if (!personalityState.draft || !personalityState.hasUnsavedChanges || personalityState.isSaving) return;
  personalityState.isSaving = true;
  updatePersonalitySaveState({ skipStatus: true });
  setPersonalityStatus("Salvando alterações…");
  try {
    const payload = await patchJSON(`${API_BASE}/personality`, {
      personality_definition: personalityState.draft,
    });
    personalityState.data = payload ?? {};
    buildPersonalityDraft(true);
    renderPersonalityPanel();
    setPersonalityStatus("Alterações salvas");
  } catch (error) {
    console.error("Falha ao salvar personalidade", error);
    setPersonalityStatus("Erro ao salvar alterações");
    window.alert("Não foi possível salvar as alterações da personalidade.");
  } finally {
    personalityState.isSaving = false;
    updatePersonalitySaveState({ skipStatus: true });
    window.setTimeout(() => {
      if (!personalityState.hasUnsavedChanges) {
        updatePersonalitySaveState();
      }
    }, 1200);
  }
}

function openGifPicker() {
  if (!elements.gifOverlay) return;
  elements.gifOverlay.classList.remove("is-hidden");
  gifState.isOpen = true;
  syncOverlayPresence();
  if (elements.gifSearch) {
    elements.gifSearch.value = gifState.filter;
    elements.gifSearch.focus();
  }
  setGifStatus(gifState.hasLoaded ? "Selecione uma reação" : "Carregando GIFs disponíveis…");
  if (!gifState.hasLoaded) {
    loadGifCatalog();
  } else {
    renderGifGrid();
  }
}

function closeGifPicker() {
  elements.gifOverlay?.classList.add("is-hidden");
  gifState.isOpen = false;
  syncOverlayPresence();
}

async function loadGifCatalog(force = false) {
  if (gifState.isLoading) return;
  if (gifState.hasLoaded && !force) {
    renderGifGrid();
    return;
  }
  gifState.isLoading = true;
  setGifStatus("Carregando GIFs disponíveis…");
  try {
    const response = await fetch(`${API_BASE}/gifs`);
    if (!response.ok) throw new Error("Falha ao carregar GIFs");
    const payload = (await response.json()) ?? [];
    gifState.gifs = Array.isArray(payload) ? payload : [];
    gifState.hasLoaded = true;
    applyGifFilter();
    setGifStatus(
      gifState.filtered.length ? `${gifState.filtered.length} GIF(s) disponíveis` : "Nenhum GIF encontrado no diretório"
    );
  } catch (error) {
    console.error("Erro ao carregar GIFs", error);
    setGifStatus("Erro ao carregar GIFs. Confira a pasta assets/gifs.");
  } finally {
    gifState.isLoading = false;
  }
}

function applyGifFilter() {
  const filter = gifState.filter.trim().toLowerCase();
  if (!filter) {
    gifState.filtered = [...gifState.gifs];
  } else {
    gifState.filtered = gifState.gifs.filter((gif) => gif.name.toLowerCase().includes(filter));
  }
  renderGifGrid();
}

function renderGifGrid() {
  if (!elements.gifList) return;
  elements.gifList.innerHTML = "";
  if (!gifState.filtered.length) {
    const placeholder = document.createElement("p");
    placeholder.className = "gif-description";
    placeholder.style.margin = "0";
    placeholder.textContent = gifState.hasLoaded
      ? "Nenhum GIF corresponde a sua busca."
      : "Ainda não há GIFs disponíveis.";
    elements.gifList.appendChild(placeholder);
    return;
  }
  gifState.filtered.forEach((gif, index) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "gif-card";
    card.dataset.gifIndex = String(index);
    const img = document.createElement("img");
    img.className = "gif-thumb";
    img.alt = `GIF ${gif.name}`;
    img.src = normalizeAssetPath(gif.url);
    img.loading = "lazy";
    const label = document.createElement("p");
    label.className = "gif-name";
    label.textContent = gif.name;
    card.append(img, label);
    elements.gifList.appendChild(card);
  });
}

function handleGifSearchInput(event) {
  if (!(event.target instanceof HTMLInputElement)) return;
  const value = event.target.value ?? "";
  gifState.filter = value;
  applyGifFilter();
  setGifStatus(
    gifState.filtered.length
      ? `${gifState.filtered.length} GIF(s) encontrados`
      : value
      ? "Nenhum GIF com esse nome"
      : "Nenhum GIF disponível"
  );
}

function handleGifListClick(event) {
  if (!(event.target instanceof Element)) return;
  const card = event.target.closest(".gif-card");
  if (!card) return;
  event.preventDefault();
  const index = Number.parseInt(card.dataset.gifIndex ?? "", 10);
  if (Number.isNaN(index)) return;
  const gifEntry = gifState.filtered[index];
  if (!gifEntry) return;
  sendGifMessage(gifEntry);
}

function handleGifUploadClick() {
  if (!elements.gifFileInput) {
    setGifStatus("Upload indisponível nesta build.");
    return;
  }
  if (gifState.isUploading) {
    setGifStatus("Um upload já está em andamento. Aguarde concluir.");
    return;
  }
  elements.gifFileInput.value = "";
  elements.gifFileInput.click();
}

async function handleGifFileChange(event) {
  const input = event.target;
  if (!(input instanceof HTMLInputElement) || !input.files || !input.files.length) {
    return;
  }
  const [file] = input.files;
  input.value = "";
  if (file) {
    await uploadGifFile(file);
  }
}

async function uploadGifFile(file) {
  if (gifState.isUploading) {
    setGifStatus("Finalize o upload atual antes de enviar outro arquivo.");
    return;
  }
  if (!file.type.includes("gif")) {
    setGifStatus("Escolha um arquivo .gif válido.");
    return;
  }
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    setGifStatus("Limite de 5 MB excedido.");
    return;
  }
  gifState.isUploading = true;
  if (elements.gifUpload) elements.gifUpload.disabled = true;
  setGifStatus(`Enviando ${file.name}…`);
  try {
    const dataUrl = await readFileAsDataUrl(file);
    const payload = await postJSON(`${API_BASE}/gifs`, {
      filename: file.name,
      data: dataUrl,
    });
    if (Array.isArray(payload?.gifs)) {
      gifState.gifs = payload.gifs;
      gifState.hasLoaded = true;
      const latestName = (payload.filename || file.name || "").replace(/\.gif$/i, "");
      if (latestName) {
        gifState.filter = latestName;
      }
      applyGifFilter();
      const label = latestName || (file.name || "novo GIF");
      setGifStatus(`GIF "${label}" disponível na grade.`);
    } else {
      setGifStatus("Upload concluído, mas a lista não pôde ser atualizada.");
    }
  } catch (error) {
    console.error("Falha ao enviar GIF", error);
    setGifStatus(buildGifUploadErrorMessage(error));
  } finally {
    gifState.isUploading = false;
    if (elements.gifUpload) elements.gifUpload.disabled = false;
  }
}

async function sendGifMessage(gifEntry) {
  const server = getActiveServer();
  const channel = getActiveChannel();
  if (!server || !channel) {
    setGifStatus("Selecione um canal antes de enviar GIFs.");
    return;
  }
  const replyToId = replyState.message?.id ?? null;
  try {
    const gifLabel = gifEntry.name || gifEntry.filename || "GIF";
    const newMessage = await postMessage({
      serverId: server.id,
      channelId: channel.id,
      authorId: "user",
      content: `[GIF] ${gifLabel}`,
      replyTo: replyToId,
      attachments: [
        {
          type: "gif",
          name: gifLabel,
          filename: gifEntry.filename,
        },
      ],
    });
    channel.messages.push(newMessage);
    clearReplyTarget();
    registerUserActivity();
    renderMessages();
    queueLouReplyAfterUserMessage(server.id, channel.id, newMessage);
    closeGifPicker();
  } catch (error) {
    console.error("Falha ao enviar GIF", error);
    setGifStatus("Erro ao enviar GIF. Confira o backend.");
  }
}

function setGifStatus(message) {
  if (!elements.gifStatus) return;
  elements.gifStatus.textContent = message || "";
}

function buildGifUploadErrorMessage(error) {
  const rawMessage = String(error?.message || error || "").toLowerCase();
  if (rawMessage.includes("5mb")) {
    return "O arquivo ultrapassa 5 MB. Escolha um GIF menor.";
  }
  if (rawMessage.includes("extensao")) {
    return "Somente arquivos .gif são aceitos.";
  }
  if (rawMessage.includes("base64")) {
    return "Falha ao ler o arquivo. Tente selecionar o GIF novamente.";
  }
  return "Não foi possível enviar o GIF agora. Confira o backend e tente de novo.";
}

function initializeAvatarUploadControls({ uploadButton, fileInput, statusNode, onSuccess }) {
  if (!uploadButton || !fileInput) {
    return;
  }
  let isUploading = false;
  const setStatus = (message) => {
    if (statusNode) {
      statusNode.textContent = message || "";
    }
  };
  uploadButton.addEventListener("click", () => {
    if (isUploading) {
      return;
    }
    fileInput.value = "";
    fileInput.click();
  });
  fileInput.addEventListener("change", async (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || !input.files || !input.files.length) {
      return;
    }
    const [file] = input.files;
    input.value = "";
    if (!file) {
      return;
    }
    isUploading = true;
    uploadButton.disabled = true;
    setStatus(`Enviando ${file.name}…`);
    try {
      const payload = await uploadAvatarAsset(file);
      if (typeof onSuccess === "function") {
        onSuccess(payload);
      }
      setStatus("Avatar enviado e preenchido automaticamente.");
    } catch (error) {
      console.error("Falha ao enviar avatar", error);
      setStatus(buildAvatarUploadErrorMessage(error));
    } finally {
      isUploading = false;
      uploadButton.disabled = false;
    }
  });
}

async function uploadAvatarAsset(file) {
  const allowedExt = ["png", "jpg", "jpeg", "gif", "webp"];
  const extension = (file.name.split(".").pop() || "").toLowerCase();
  const isImageType = file.type.startsWith("image/");
  if (!isImageType && !allowedExt.includes(extension)) {
    throw new Error("Extensoes permitidas: png, jpg, jpeg, gif, webp");
  }
  const maxSize = 2 * 1024 * 1024;
  if (file.size > maxSize) {
    throw new Error("Arquivo acima de 2MB");
  }
  const dataUrl = await readFileAsDataUrl(file);
  return postJSON(`${API_BASE}/avatars`, {
    filename: file.name,
    data: dataUrl,
  });
}

function buildAvatarUploadErrorMessage(error) {
  const raw = String(error?.message || error || "").toLowerCase();
  if (raw.includes("2mb")) {
    return "O arquivo ultrapassa 2 MB.";
  }
  if (raw.includes("extens")) {
    return "Formatos aceitos: png, jpg, jpeg, gif e webp.";
  }
  if (raw.includes("base64")) {
    return "Não consegui ler o arquivo. Tente selecionar novamente.";
  }
  return "Não foi possível enviar o avatar agora. Confira o backend.";
}

function normalizeUploadedAvatarPath(payload) {
  if (!payload) return "";
  if (payload.path) {
    return payload.path.replace(/^\/+/, "");
  }
  if (payload.filename) {
    return `assets/avatars/${payload.filename}`;
  }
  return "";
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
      } else {
        reject(new Error("Não foi possível converter o arquivo."));
      }
    };
    reader.onerror = () => reject(new Error("Falha ao ler o arquivo selecionado."));
    reader.readAsDataURL(file);
  });
}

function handleGifEscapeKey(event) {
  if (event.key === "Escape" && gifState.isOpen) {
    closeGifPicker();
  }
}

function openContextPanel() {
  if (!elements.contextOverlay) return;
  elements.contextOverlay.classList.remove("is-hidden");
  contextState.isOpen = true;
  if (!contextState.hasLoaded) {
    loadContextSnapshot();
  } else {
    renderContextLists();
  }
  syncOverlayPresence();
}

function closeContextPanel() {
  elements.contextOverlay?.classList.add("is-hidden");
  contextState.isOpen = false;
  syncOverlayPresence();
}

async function loadContextSnapshot(force = false) {
  if (contextState.isLoading) return;
  if (contextState.hasLoaded && !force) {
    renderContextLists();
    return;
  }
  contextState.isLoading = true;
  setContextStatus("Carregando contexto compartilhado…");
  try {
    const response = await fetch(`${API_BASE}/context`);
    if (!response.ok) throw new Error("Falha ao carregar contexto");
    const snapshot = await response.json();
    contextState.snapshot = normalizeContextSnapshot(snapshot);
    contextState.hasLoaded = true;
    renderContextLists();
    setContextStatus("Contexto sincronizado");
  } catch (error) {
    console.error("Falha ao carregar contexto", error);
    setContextStatus("Erro ao carregar contexto");
  } finally {
    contextState.isLoading = false;
  }
}

function normalizeContextSnapshot(snapshot) {
  return {
    long_term: Array.isArray(snapshot?.long_term) ? [...snapshot.long_term] : [],
    short_term: Array.isArray(snapshot?.short_term) ? [...snapshot.short_term] : [],
    styles: Array.isArray(snapshot?.styles) ? [...snapshot.styles] : [],
  };
}

function renderContextLists() {
  renderContextList(elements.contextListShort, contextState.snapshot.short_term, "Nenhuma memória recente");
  renderContextList(elements.contextListLong, contextState.snapshot.long_term, "Nenhum registro de longo prazo");
  renderContextList(elements.contextListStyle, contextState.snapshot.styles, "Nenhuma gíria cadastrada");
}

function renderContextList(listNode, items, emptyLabel) {
  if (!listNode) return;
  listNode.innerHTML = "";
  if (!items || !items.length) {
    const placeholder = document.createElement("li");
    placeholder.textContent = emptyLabel;
    placeholder.style.opacity = "0.7";
    listNode.appendChild(placeholder);
    return;
  }
  items.forEach((item) => {
    const entry = document.createElement("li");
    entry.textContent = item;
    listNode.appendChild(entry);
  });
}

function setContextStatus(message) {
  if (!elements.contextStatus) return;
  elements.contextStatus.textContent = message ?? "";
}

function refreshProactiveWatcher(options = {}) {
  const channel = getActiveChannel();
  if (!channel) {
    stopProactiveTimer();
    return;
  }
  if (options.resetAttempts) {
    proactiveState.attempt = 0;
    proactiveState.proactiveMessagesSent = 0;
    proactiveState.absenceQuestionSent = false;
    proactiveState.awaitingUserResponse = false;
  }
  proactiveState.lastUserActivity = Date.now();
  startProactiveTimer();
}

function registerUserActivity() {
  refreshProactiveWatcher({ resetAttempts: true });
  availabilityState.lastUserMessageAt = Date.now();
  availabilityState.pendingShortCycle = true;
  if (typeof window !== "undefined" && availabilityState.manualDowntimeTimerId) {
    window.clearTimeout(availabilityState.manualDowntimeTimerId);
    availabilityState.manualDowntimeTimerId = null;
  }
  if (availabilityState.isManualDowntimeActive) {
    availabilityState.isManualDowntimeActive = false;
    updateAiAvailabilityUi();
  }
  if (availabilityState.status === "away") {
    clearAvailabilityShiftTimer();
    scheduleReturnToAvailableAfterUserMessage();
    return;
  }
  if (!availabilityState.isManualDowntimeActive) {
    scheduleAvailabilityShift();
  }
}

function queueLouReplyAfterUserMessage(serverId, channelId, referenceMessage) {
  if (!serverId || !channelId) return;
  if (availabilityState.status === "away") {
    availabilityState.pendingLouReply = { serverId, channelId, referenceMessage };
    return;
  }
  scheduleLouReplyCountdown({ serverId, channelId, referenceMessage });
}

function scheduleLouReplyCountdown({ serverId, channelId, referenceMessage }) {
  if (!serverId || !channelId) return;
  cancelLouReplyTimer();
  cancelLouReplyRequest();
  interruptLouOutput();
  louReplyState.serverId = serverId;
  louReplyState.channelId = channelId;
  louReplyState.referenceMessage = referenceMessage;
  const baseDelay = randomBetween(louReplyState.debounceRange.min, louReplyState.debounceRange.max);
  const waitMs = baseDelay + getAvailabilityResponseLag();
  louReplyState.generationToken += 1;
  const token = louReplyState.generationToken;
  louReplyState.timerId = window.setTimeout(() => {
    louReplyState.timerId = null;
    triggerLouReplyFlow(serverId, channelId, referenceMessage, { token });
  }, waitMs);
}

function cancelLouReplyTimer() {
  if (louReplyState.timerId) {
    window.clearTimeout(louReplyState.timerId);
    louReplyState.timerId = null;
  }
}

function cancelLouReplyRequest() {
  if (louReplyState.abortController) {
    louReplyState.abortController.abort();
    louReplyState.abortController = null;
  }
}

function interruptLouOutput() {
  if (louReplyState.outputController) {
    louReplyState.outputController.cancel();
    louReplyState.outputController = null;
  }
}

function startProactiveTimer() {
  window.clearTimeout(proactiveState.timerId);
  if (!getActiveChannel()) return;
  if (proactiveState.awaitingUserResponse) return;
  const nextKind = getNextProactiveKind();
  if (!nextKind) return;
  const delay = getProactiveDelay();
  proactiveState.timerId = window.setTimeout(handleProactiveTimeout, delay);
}

function stopProactiveTimer() {
  if (proactiveState.timerId) {
    window.clearTimeout(proactiveState.timerId);
    proactiveState.timerId = null;
  }
}

function getProactiveDelay() {
  return PROACTIVE_DELAYS[Math.min(proactiveState.attempt, PROACTIVE_DELAYS.length - 1)];
}

function getNextProactiveKind() {
  if (proactiveState.proactiveMessagesSent < MAX_PROACTIVE_MESSAGES) {
    return "proactive";
  }
  if (!proactiveState.absenceQuestionSent) {
    return "absence";
  }
  return null;
}

function handleProactiveTimeout() {
  if (!shouldTriggerProactive()) {
    startProactiveTimer();
    return;
  }
  triggerProactiveMessage();
}

function shouldTriggerProactive() {
  const channel = getActiveChannel();
  if (!channel) return false;
  const idleFor = Date.now() - proactiveState.lastUserActivity;
  return idleFor >= getProactiveDelay();
}

async function triggerProactiveMessage(options = {}) {
  const { manual = false } = options;
  const server = getActiveServer();
  const channel = getActiveChannel();
  if (!server || !channel) return;
  if (availabilityState.status === "away") {
    if (!manual) {
      startProactiveTimer();
    }
    return;
  }
  const nextKind = manual ? "proactive" : getNextProactiveKind();
  if (!manual && (!nextKind || proactiveState.awaitingUserResponse)) {
    stopProactiveTimer();
    return;
  }
  if (proactiveState.requestInFlight) return;
  proactiveState.requestInFlight = true;
  const requestStartedAt = Date.now();
  const targetInitialDelay =
    randomBetween(LOU_TYPING_INITIAL_DELAY.min, LOU_TYPING_INITIAL_DELAY.max) + getAvailabilityTypingLag();
  try {
    const message = await postJSON(`${API_BASE}/proactive`, {
      serverId: server.id,
      channelId: channel.id,
      attempt: manual ? 0 : proactiveState.attempt,
    });
    const elapsed = Date.now() - requestStartedAt;
    const remainingInitialWait = Math.max(targetInitialDelay - elapsed, 0);
    await playLouTypingSequence(server.id, channel.id, [message], { initialWait: remainingInitialWait });
    proactiveState.lastUserActivity = Date.now();
    if (!manual) {
      if (nextKind === "proactive") {
        proactiveState.proactiveMessagesSent = Math.min(
          proactiveState.proactiveMessagesSent + 1,
          MAX_PROACTIVE_MESSAGES
        );
      } else if (nextKind === "absence") {
        proactiveState.absenceQuestionSent = true;
        proactiveState.awaitingUserResponse = true;
      }
      proactiveState.attempt += 1;
    }
  } catch (error) {
    console.error("Falha ao gerar mensagem proativa", error);
  } finally {
    proactiveState.requestInFlight = false;
    if (manual) {
      startProactiveTimer();
      return;
    }
    if (proactiveState.awaitingUserResponse) {
      stopProactiveTimer();
      return;
    }
    if (getNextProactiveKind()) {
      startProactiveTimer();
    } else {
      stopProactiveTimer();
    }
  }
}

function openDialog(template) {
  if (!elements.modalRoot) return null;
  closeDialog();
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = template;
  const dialog = backdrop.querySelector(".lou-dialog");
  if (!dialog) return null;
  dialog.addEventListener("click", (event) => event.stopPropagation());
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop) closeDialog();
  });
  elements.modalRoot.appendChild(backdrop);
  modalState.node = backdrop;
  modalState.escHandler = (event) => {
    if (event.key === "Escape") closeDialog();
  };
  document.addEventListener("keydown", modalState.escHandler);
  syncOverlayPresence();
  return backdrop;
}

function closeDialog() {
  if (modalState.node) {
    modalState.node.remove();
    modalState.node = null;
  }
  if (modalState.escHandler) {
    document.removeEventListener("keydown", modalState.escHandler);
    modalState.escHandler = null;
  }
  syncOverlayPresence();
}

async function postJSON(url, payload, options) {
  return sendJSON(url, "POST", payload, options);
}

async function patchJSON(url, payload, options) {
  return sendJSON(url, "PATCH", payload, options);
}

async function deleteJSON(url, options) {
  return sendJSON(url, "DELETE", undefined, options);
}

async function sendJSON(url, method, payload, requestOptions = {}) {
  const fetchOptions = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (payload !== undefined) {
    fetchOptions.body = JSON.stringify(payload);
  }
  if (requestOptions?.signal) {
    fetchOptions.signal = requestOptions.signal;
  }
  const response = await fetch(url, fetchOptions);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Erro ${response.status}`);
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}
