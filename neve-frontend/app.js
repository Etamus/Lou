const API_BASE = "/api";
let profiles = {};

const state = {
  servers: [],
  activeServerId: null,
  activeChannelId: null,
  isLoading: true,
};

const elements = {
  serverRail: document.querySelector("[data-role=server-rail]"),
  channelList: document.querySelector("[data-role=channel-list]"),
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
  contextRefresh: document.querySelector("[data-role=context-refresh]"),
  contextStatus: document.querySelector("[data-role=context-status]"),
  contextListShort: document.querySelector("[data-role=context-list-short]"),
  contextListLong: document.querySelector("[data-role=context-list-long]"),
  contextListStyle: document.querySelector("[data-role=context-list-style]"),
  proactiveTrigger: document.querySelector("[data-role=proactive-trigger]"),
  gifButton: document.querySelector("[data-role=gif-button]"),
  gifOverlay: document.querySelector("[data-role=gif-overlay]"),
  gifPanel: document.querySelector("[data-role=gif-panel]"),
  gifClose: document.querySelector("[data-role=gif-close]"),
  gifRefresh: document.querySelector("[data-role=gif-refresh]"),
  gifUpload: document.querySelector("[data-role=gif-upload]"),
  gifStatus: document.querySelector("[data-role=gif-status]"),
  gifList: document.querySelector("[data-role=gif-list]"),
  gifSearch: document.querySelector("[data-role=gif-search]"),
  gifFileInput: document.querySelector("[data-role=gif-file-input]"),
  louflixToggle: document.querySelector("[data-role=louflix-toggle]"),
  louflixOverlay: document.querySelector("[data-role=louflix-overlay]"),
  louflixPanel: document.querySelector("[data-role=louflix-panel]"),
  louflixClose: document.querySelector("[data-role=louflix-close]"),
  louflixRefresh: document.querySelector("[data-role=louflix-refresh]"),
  louflixStatus: document.querySelector("[data-role=louflix-status]"),
  louflixTitle: document.querySelector("[data-role=louflix-title]"),
  louflixDescription: document.querySelector("[data-role=louflix-description]"),
  louflixPoster: document.querySelector("[data-role=louflix-poster]"),
  louflixVideo: document.querySelector("[data-role=louflix-video]"),
  louflixTriggerList: document.querySelector("[data-role=louflix-trigger-list]"),
  louflixTriggerCount: document.querySelector("[data-role=louflix-trigger-count]"),
  louflixPlaybackIndicator: document.querySelector("[data-role=louflix-playback-indicator]"),
  louflixCommentForm: document.querySelector("[data-role=louflix-comment-form]"),
  louflixTimestampInput: document.querySelector("[data-role=louflix-timestamp-input]"),
  louflixSecondsInput: document.querySelector("[data-role=louflix-seconds-input]"),
  louflixPromptPreview: document.querySelector("[data-role=louflix-prompt-preview]"),
  louflixCommentInput: document.querySelector("[data-role=louflix-comment-input]"),
  louflixCommentsList: document.querySelector("[data-role=louflix-comments-list]"),
  louflixCommentSubmit: document.querySelector("[data-role=louflix-comment-submit]"),
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

const LOUFLIX_PROMPT_PLACEHOLDER = "Selecione um trigger para preencher automaticamente.";

const louflixState = {
  session: null,
  isLoading: false,
  isOpen: false,
  isSubmitting: false,
  selectedTriggerIndex: null,
  selectedPrompt: "",
};

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
const proactiveState = {
  timerId: null,
  attempt: 0,
  maxAttempts: 3,
  lastUserActivity: Date.now(),
  requestInFlight: false,
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
const LOU_TYPING_INITIAL_DELAY = { min: 900, max: 2000 };
const LOU_TYPING_BURST_DELAY = { min: 1100, max: 2200 };
const LOU_TYPING_BETWEEN_DELAY = { min: 350, max: 900 };

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
  rail.innerHTML = "";
  state.servers.forEach((server) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = server.shortName ?? server.name.slice(0, 2).toUpperCase();
    if (server.id === state.activeServerId) button.classList.add("active");
    button.addEventListener("click", () => {
      if (state.activeServerId === server.id) return;
      state.activeServerId = server.id;
      state.activeChannelId = server.channels[0]?.id ?? null;
      renderServers();
      renderChannels();
      renderChatArea();
      refreshProactiveWatcher();
    });
    rail.appendChild(button);
  });
  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.innerHTML = '<i class="fas fa-plus" aria-hidden="true"></i>';
  addButton.title = "Criar servidor";
  addButton.setAttribute("aria-label", "Criar servidor");
  addButton.addEventListener("click", handleCreateServerFlow);
  rail.appendChild(addButton);
}

function renderChannels() {
  const server = getActiveServer();
  setBinding(bindings.serverName, server?.name ?? "Sem servidor");
  if (elements.channelCreateButton) {
    elements.channelCreateButton.disabled = !server;
  }

  const list = elements.channelList;
  list.innerHTML = "";
  if (!server) return;

  server.channels.forEach((channel) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "channel-button";
    button.dataset.channelId = channel.id;
    if (channel.id === state.activeChannelId) button.classList.add("active");
    button.innerHTML = `
      <span class="channel-label">
        <span class="channel-badge">#</span>
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
}

function renderChatArea() {
  const channel = getActiveChannel();
  if (!channel || channel.id !== replyState.channelId) {
    clearReplyTarget();
  }
  setBinding(bindings.channelName, channel ? `#${channel.name}` : "Selecione um canal");
  setBinding(bindings.channelTopic, channel?.topic ?? "");
  elements.messageInput.placeholder = channel ? `Conversar em #${channel.name}` : "Selecione um canal";
  renderMessages();
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
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
    showEmptyState("Nenhum canal selecionado", "Crie ou escolha um servidor para visualizar os canais.");
    return;
  }

  let lastDayLabel = "";
  if (channel.messages.length === 0) {
    showEmptyState("Histórico limpo", "Envie a primeira mensagem desse canal para iniciar o log.");
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

function formatSecondsAsTimestamp(totalSeconds) {
  const safeSeconds = Math.max(0, Number.isFinite(totalSeconds) ? Math.floor(totalSeconds) : 0);
  const hours = Math.floor(safeSeconds / 3600)
    .toString()
    .padStart(2, "0");
  const minutes = Math.floor((safeSeconds % 3600) / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(safeSeconds % 60)
    .toString()
    .padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

function parseTimestampToSeconds(value) {
  if (!value) return 0;
  const sanitized = value.trim();
  if (!sanitized) return 0;
  const tokens = sanitized.split(":").map((part) => Number.parseInt(part, 10));
  if (tokens.some((token) => Number.isNaN(token))) return 0;
  if (tokens.length === 3) {
    const [hours, minutes, seconds] = tokens;
    return hours * 3600 + minutes * 60 + seconds;
  }
  if (tokens.length === 2) {
    const [minutes, seconds] = tokens;
    return minutes * 60 + seconds;
  }
  return tokens[0] ?? 0;
}

function formatLouflixDate(isoString) {
  if (!isoString) return "";
  const parsed = new Date(isoString);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
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
  const text = elements.messageInput.value.trim();
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
    elements.messageInput.value = "";
    autoResizeTextarea();
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
  const targetInitialDelay = randomBetween(LOU_TYPING_INITIAL_DELAY.min, LOU_TYPING_INITIAL_DELAY.max);
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

function autoResizeTextarea() {
  const textarea = elements.messageInput;
  if (!textarea) return;
  if (!textarea.dataset.baseHeight) {
    textarea.dataset.baseHeight = String(textarea.clientHeight || 32);
  }
  const baseHeight = Number(textarea.dataset.baseHeight) || 32;
  textarea.style.height = "auto";
  const nextHeight = Math.min(Math.max(textarea.scrollHeight, baseHeight), 96);
  textarea.style.height = `${nextHeight}px`;
}

function bindEvents() {
  elements.messageForm.addEventListener("submit", handleFormSubmit);
  elements.messageInput.addEventListener("input", autoResizeTextarea);
  elements.messageInput.addEventListener("keydown", handleComposerKeyDown);
  elements.channelCreateButton?.addEventListener("click", handleCreateChannelFlow);
  elements.channelList?.addEventListener("click", handleChannelListClick);
  elements.channelList?.addEventListener("keydown", handleChannelListKeyDown);
  elements.messageList?.addEventListener("click", handleMessageListClick);
  elements.serverSettingsButton?.addEventListener("click", () => {
    const server = getActiveServer();
    if (!server) return;
    openServerSettingsDialog(server);
  });
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
  elements.contextRefresh?.addEventListener("click", () => loadContextSnapshot(true));
  elements.proactiveTrigger?.addEventListener("click", () => triggerProactiveMessage({ manual: true }));
  elements.louflixToggle?.addEventListener("click", openLouflixPanel);
  elements.louflixClose?.addEventListener("click", closeLouflixPanel);
  elements.louflixOverlay?.addEventListener("click", (event) => {
    if (event.target === elements.louflixOverlay) {
      closeLouflixPanel();
    }
  });
  elements.louflixRefresh?.addEventListener("click", () => loadLouflixSession(true));
  elements.louflixTriggerList?.addEventListener("click", handleLouflixTriggerListClick);
  elements.louflixCommentForm?.addEventListener("submit", handleLouflixCommentSubmit);
  elements.louflixPanel?.addEventListener("click", handleLouflixPanelClick);
  if (elements.louflixVideo) {
    elements.louflixVideo.addEventListener("timeupdate", updateLouflixPlaybackIndicator);
    elements.louflixVideo.addEventListener("loadedmetadata", updateLouflixPlaybackIndicator);
  }
  document.addEventListener("keydown", handleLouflixEscapeKey);
  elements.gifButton?.addEventListener("click", openGifPicker);
  elements.gifClose?.addEventListener("click", closeGifPicker);
  elements.gifRefresh?.addEventListener("click", () => loadGifCatalog(true));
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
}

function handleComposerKeyDown(event) {
  if (event.key !== "Enter") return;
  if (event.shiftKey) return;
  event.preventDefault();
  if (elements.messageForm) {
    elements.messageForm.requestSubmit();
  }
}

async function init() {
  bindEvents();
  autoResizeTextarea();
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

async function handleCreateServerFlow() {
  const name = window.prompt("Nome do novo servidor:");
  if (!name || !name.trim()) return;
  try {
    const server = await postJSON(`${API_BASE}/servers`, { name: name.trim() });
    state.servers.push(server);
    state.activeServerId = server.id;
    state.activeChannelId = server.channels[0]?.id ?? null;
    renderServers();
    renderChannels();
    renderChatArea();
    refreshProactiveWatcher({ resetAttempts: true });
  } catch (error) {
    console.error("Falha ao criar servidor", error);
  }
}

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
  const name = window.prompt("Nome do novo canal:");
  if (!name || !name.trim()) return;
  try {
    const channel = await postJSON(`${API_BASE}/servers/${server.id}/channels`, { name: name.trim() });
    server.channels.push(channel);
    state.activeChannelId = channel.id;
    renderChannels();
    renderChatArea();
    refreshProactiveWatcher({ resetAttempts: true });
  } catch (error) {
    console.error("Falha ao criar canal", error);
  }
}

function openChannelRenameDialog(server, channel) {
  const safeName = escapeHTML(channel.name);
  const template = `
    <div class="lou-dialog" role="dialog" aria-modal="true">
      <div class="lou-dialog__header">
        <div>
          <h2 class="lou-dialog__title">Renomear canal</h2>
          <p class="lou-dialog__subtitle">#${safeName}</p>
        </div>
        <button class="lou-dialog__close" type="button" data-action="close">×</button>
      </div>
      <form class="lou-form" data-role="channel-form">
        <label class="lou-field">
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
          <p class="lou-dialog__subtitle">#${safeName}</p>
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
  const safeAvatar = escapeHTML(server.avatar ?? "");
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
        <div class="lou-profile-preview">
          <div class="lou-avatar-preview" data-role="server-avatar-preview"></div>
          <div class="lou-avatar-actions">
            <p class="lou-hint">Envie um PNG/JPG (até 2 MB) ou cole um caminho manual.</p>
            <button class="ghost-button" type="button" data-action="upload-avatar">Enviar imagem</button>
            <input type="file" data-role="server-avatar-file" accept="image/png,image/jpeg,image/webp,image/gif" hidden />
            <p class="lou-hint" data-role="avatar-status"></p>
          </div>
        </div>
        <label class="lou-field">
          <span class="lou-label">Nome do servidor</span>
          <input class="lou-input" name="name" value="${safeName}" maxlength="48" autocomplete="off" />
        </label>
        <label class="lou-field">
          <span class="lou-label">Avatar (caminho relativo)</span>
          <input class="lou-input" name="avatar" value="${safeAvatar}" placeholder="assets/avatars/lou.png" autocomplete="off" />
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
  const avatarInput = form.querySelector('input[name="avatar"]');
  const avatarPreview = dialog.querySelector('[data-role="server-avatar-preview"]');
  const avatarStatus = dialog.querySelector('[data-role="avatar-status"]');
  const avatarUploadButton = dialog.querySelector('[data-action="upload-avatar"]');
  const avatarFileInput = dialog.querySelector('[data-role="server-avatar-file"]');
  const deleteButton = form.querySelector('[data-action="delete"]');
  const cancelButtons = dialog.querySelectorAll('[data-action="close"],[data-action="cancel"]');
  cancelButtons.forEach((btn) => btn.addEventListener("click", closeDialog));
  nameInput.focus();
  nameInput.select();

  const updateServerAvatarPreview = (path) => {
    if (!avatarPreview) return;
    avatarPreview.innerHTML = "";
    const img = document.createElement("img");
    img.alt = `Avatar do servidor ${serverName}`;
    const selectedPath = path && path.trim() ? path.trim() : "assets/avatars/default.png";
    img.src = normalizeAssetPath(selectedPath);
    img.addEventListener("error", () => {
      img.remove();
      avatarPreview.textContent = serverName.slice(0, 2).toUpperCase();
    });
    avatarPreview.appendChild(img);
  };

  if (avatarInput) {
    updateServerAvatarPreview(avatarInput.value || server.avatar);
    avatarInput.addEventListener("input", () => {
      updateServerAvatarPreview(avatarInput.value);
      if (avatarStatus) avatarStatus.textContent = "";
    });
  }

  initializeAvatarUploadControls({
    uploadButton: avatarUploadButton,
    fileInput: avatarFileInput,
    statusNode: avatarStatus,
    onSuccess: (payload) => {
      if (!avatarInput) return;
      const normalized = normalizeUploadedAvatarPath(payload);
      avatarInput.value = normalized;
      updateServerAvatarPreview(normalized);
    },
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const newName = nameInput.value.trim();
    if (!newName) {
      nameInput.focus();
      return;
    }
    const avatarValue = avatarInput?.value.trim();
    const payload = { name: newName };
    if (avatarValue) {
      payload.avatar = avatarValue;
    }
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
          <p class="lou-hint">Envie PNG/JPG (até 2 MB) ou cole um caminho existente.</p>
          <button class="ghost-button" type="button" data-action="upload-avatar">Enviar imagem</button>
          <input type="file" data-role="profile-avatar-file" accept="image/png,image/jpeg,image/webp,image/gif" hidden />
          <p class="lou-hint" data-role="avatar-status"></p>
        </div>
      </div>
      <form class="lou-form" data-role="profile-form">
        <label class="lou-field">
          <span class="lou-label">Nome</span>
          <input class="lou-input" name="name" maxlength="48" autocomplete="off" />
        </label>
        <label class="lou-field">
          <span class="lou-label">Avatar (caminho relativo)</span>
          <input class="lou-input" name="avatar" placeholder="assets/avatars/lou.png" autocomplete="off" />
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
  const avatarInput = form.querySelector('input[name="avatar"]');
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
    avatarInput.value = profile.avatar ?? "";
    updateAvatarPreview(avatarInput.value || profile.avatar);
    if (avatarStatus) avatarStatus.textContent = "";
  };

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      currentKey = tab.dataset.profileKey;
      syncTabs();
    });
  });

  avatarInput.addEventListener("input", () => {
    updateAvatarPreview(avatarInput.value);
    if (avatarStatus) avatarStatus.textContent = "";
  });

  initializeAvatarUploadControls({
    uploadButton: avatarUploadButton,
    fileInput: avatarFileInput,
    statusNode: avatarStatus,
    onSuccess: (payload) => {
      const normalized = normalizeUploadedAvatarPath(payload);
      avatarInput.value = normalized;
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
    const payload = { name: newName, avatar: avatarInput.value.trim() || null };
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
  if (!personalityState.data) {
    await loadPersonalityData();
    return;
  }
  buildPersonalityDraft(true);
  renderPersonalityPanel();
}

function closePersonalityEditor() {
  elements.personalityOverlay?.classList.add("is-hidden");
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
    setPersonalityStatus("Ficha carregada");
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
    const message = personalityState.hasUnsavedChanges
      ? "Alterações não salvas"
      : "Tudo sincronizado com personality_prompt.json";
    setPersonalityStatus(message);
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

function openLouflixPanel() {
  if (!elements.louflixOverlay) return;
  elements.louflixOverlay.classList.remove("is-hidden");
  louflixState.isOpen = true;
  setLouflixStatus(louflixState.session ? "Sessão carregada" : "Carregando sessão…");
  if (!louflixState.session || louflixState.session.triggers === undefined) {
    loadLouflixSession();
  } else {
    renderLouflixSession();
  }
}

function closeLouflixPanel() {
  elements.louflixOverlay?.classList.add("is-hidden");
  louflixState.isOpen = false;
  if (elements.louflixVideo && typeof elements.louflixVideo.pause === "function") {
    elements.louflixVideo.pause();
  }
}

async function loadLouflixSession(force = false) {
  if (louflixState.isLoading) return;
  if (louflixState.session && !force) {
    renderLouflixSession();
    return;
  }
  louflixState.isLoading = true;
  setLouflixStatus("Carregando sessão LouFlix…");
  try {
    const response = await fetch(`${API_BASE}/louflix/session`);
    if (!response.ok) throw new Error("Falha ao carregar dados do LouFlix");
    const payload = await response.json();
    louflixState.session = {
      ...payload,
      triggers: Array.isArray(payload?.triggers) ? payload.triggers : [],
      comments: Array.isArray(payload?.comments) ? payload.comments : [],
    };
    louflixState.selectedTriggerIndex = null;
    louflixState.selectedPrompt = "";
    renderLouflixSession();
    setLouflixStatus("Sessão sincronizada com o backend");
  } catch (error) {
    console.error("Falha ao carregar LouFlix", error);
    setLouflixStatus("Erro ao carregar sessão. Tente novamente.");
  } finally {
    louflixState.isLoading = false;
  }
}

function renderLouflixSession() {
  if (!louflixState.session) return;
  const { title, description, poster, video, triggers = [], comments = [] } = louflixState.session;
  if (elements.louflixTitle) elements.louflixTitle.textContent = title || "Sessão";
  if (elements.louflixDescription) elements.louflixDescription.textContent = description || "";
  if (elements.louflixPoster) {
    const posterPath = poster ? normalizeAssetPath(poster) : "";
    elements.louflixPoster.style.backgroundImage = posterPath ? `url('${posterPath}')` : "";
  }
  if (elements.louflixVideo) {
    const normalizedVideo = video ? normalizeAssetPath(video) : "";
    if (normalizedVideo && elements.louflixVideo.getAttribute("src") !== normalizedVideo) {
      elements.louflixVideo.src = normalizedVideo;
      elements.louflixVideo.load();
    }
    if (poster) {
      elements.louflixVideo.poster = normalizeAssetPath(poster);
    } else {
      elements.louflixVideo.removeAttribute("poster");
    }
  }
  renderLouflixTriggers(triggers);
  renderLouflixComments(comments);
  resetLouflixPromptPreview();
  updateLouflixPlaybackIndicator();
}

function renderLouflixTriggers(triggers) {
  if (!elements.louflixTriggerList) return;
  elements.louflixTriggerList.innerHTML = "";
  const list = Array.isArray(triggers) ? [...triggers] : [];
  if (!list.length) {
    const placeholder = document.createElement("p");
    placeholder.className = "louflix-comment-empty";
    placeholder.textContent = "Nenhum trigger configurado.";
    elements.louflixTriggerList.appendChild(placeholder);
  } else {
    list.forEach((trigger, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "louflix-trigger";
      if (index === louflixState.selectedTriggerIndex) {
        button.classList.add("is-active");
      }
      button.dataset.triggerIndex = String(index);
      const time = document.createElement("span");
      time.className = "louflix-trigger-time";
      time.textContent = trigger.timestamp || formatSecondsAsTimestamp(trigger.seconds ?? 0);
      const prompt = document.createElement("p");
      prompt.className = "louflix-trigger-prompt";
      prompt.textContent = trigger.prompt || "Sem descrição";
      button.append(time, prompt);
      elements.louflixTriggerList.appendChild(button);
    });
  }
  if (elements.louflixTriggerCount) {
    elements.louflixTriggerCount.textContent = list.length ? `${list.length} eventos` : "Sem eventos";
  }
}

function renderLouflixComments(comments) {
  if (!elements.louflixCommentsList) return;
  elements.louflixCommentsList.innerHTML = "";
  const list = Array.isArray(comments) ? [...comments] : [];
  if (!list.length) {
    const placeholder = document.createElement("p");
    placeholder.className = "louflix-comment-empty";
    placeholder.textContent = "Nenhum comentário enviado ainda.";
    elements.louflixCommentsList.appendChild(placeholder);
    return;
  }
  list
    .sort((a, b) => Number(a.seconds ?? 0) - Number(b.seconds ?? 0))
    .forEach((comment) => {
      const item = document.createElement("article");
      item.className = "louflix-comment-item";
      const meta = document.createElement("div");
      meta.className = "louflix-comment-meta";
      const timestamp = document.createElement("span");
      timestamp.textContent = comment.timestamp || formatSecondsAsTimestamp(comment.seconds ?? 0);
      const createdAt = document.createElement("span");
      createdAt.textContent = formatLouflixDate(comment.created_at);
      meta.append(timestamp, createdAt);
      const prompt = (comment.trigger_prompt || "").trim();
      if (prompt) {
        const promptNode = document.createElement("p");
        promptNode.className = "louflix-comment-prompt";
        promptNode.textContent = prompt;
        item.appendChild(promptNode);
      }
      const body = document.createElement("p");
      body.className = "louflix-comment-text";
      body.textContent = comment.comment || "";
      item.prepend(meta);
      item.appendChild(body);
      elements.louflixCommentsList.appendChild(item);
    });
}

function handleLouflixTriggerListClick(event) {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest(".louflix-trigger");
  if (!button) return;
  event.preventDefault();
  const index = Number.parseInt(button.dataset.triggerIndex ?? "", 10);
  if (Number.isNaN(index)) return;
  selectLouflixTrigger(index);
}

function selectLouflixTrigger(index) {
  if (!louflixState.session || !Array.isArray(louflixState.session.triggers)) return;
  const trigger = louflixState.session.triggers[index];
  if (!trigger) return;
  louflixState.selectedTriggerIndex = index;
  louflixState.selectedPrompt = trigger.prompt || "";
  renderLouflixTriggers(louflixState.session.triggers);
  updateLouflixFormFromTrigger(trigger);
  if (elements.louflixVideo && typeof trigger.seconds === "number") {
    try {
      elements.louflixVideo.currentTime = trigger.seconds;
      elements.louflixVideo.focus?.();
    } catch (error) {
      console.error("Não foi possível ajustar o tempo do vídeo", error);
    }
  }
}

function updateLouflixFormFromTrigger(trigger) {
  const timestamp = trigger.timestamp || formatSecondsAsTimestamp(trigger.seconds ?? 0);
  if (elements.louflixTimestampInput) {
    elements.louflixTimestampInput.value = timestamp;
  }
  if (elements.louflixSecondsInput) {
    elements.louflixSecondsInput.value = String(trigger.seconds ?? parseTimestampToSeconds(timestamp));
  }
  if (elements.louflixPromptPreview) {
    elements.louflixPromptPreview.textContent = trigger.prompt || LOUFLIX_PROMPT_PLACEHOLDER;
  }
}

function resetLouflixPromptPreview() {
  if (!elements.louflixPromptPreview) return;
  const label = louflixState.selectedPrompt || LOUFLIX_PROMPT_PLACEHOLDER;
  elements.louflixPromptPreview.textContent = label;
}

function handleLouflixPanelClick(event) {
  event.stopPropagation();
  if (!(event.target instanceof Element)) return;
  const captureButton = event.target.closest("[data-role=louflix-capture-time]");
  if (!captureButton) return;
  event.preventDefault();
  captureLouflixTimestamp();
}

function captureLouflixTimestamp() {
  if (!elements.louflixVideo) return;
  const seconds = Math.floor(elements.louflixVideo.currentTime || 0);
  applyLouflixTimestamp(seconds);
}

function applyLouflixTimestamp(seconds) {
  const timestamp = formatSecondsAsTimestamp(seconds);
  if (elements.louflixTimestampInput) {
    elements.louflixTimestampInput.value = timestamp;
  }
  if (elements.louflixSecondsInput) {
    elements.louflixSecondsInput.value = String(seconds);
  }
}

function updateLouflixPlaybackIndicator() {
  if (!elements.louflixVideo || !elements.louflixPlaybackIndicator) return;
  const current = Math.floor(elements.louflixVideo.currentTime || 0);
  const duration = Number.isFinite(elements.louflixVideo.duration)
    ? Math.floor(elements.louflixVideo.duration || 0)
    : null;
  const currentLabel = formatSecondsAsTimestamp(current);
  elements.louflixPlaybackIndicator.textContent = duration
    ? `${currentLabel} / ${formatSecondsAsTimestamp(duration)}`
    : currentLabel;
}

function setLouflixStatus(message) {
  if (!elements.louflixStatus) return;
  elements.louflixStatus.textContent = message || "";
}

async function handleLouflixCommentSubmit(event) {
  event.preventDefault();
  if (louflixState.isSubmitting) return;
  const commentInputValue = elements.louflixCommentInput?.value ?? "";
  const commentText = commentInputValue.trim();
  if (!commentText) {
    setLouflixStatus("Escreva um comentário antes de enviar.");
    elements.louflixCommentInput?.focus();
    return;
  }
  const timestampValue = (elements.louflixTimestampInput?.value ?? "").trim();
  const secondsHidden = (elements.louflixSecondsInput?.value ?? "").trim();
  let seconds = secondsHidden ? Number.parseInt(secondsHidden, 10) : parseTimestampToSeconds(timestampValue);
  if (!Number.isFinite(seconds)) seconds = 0;
  const timestamp = timestampValue || formatSecondsAsTimestamp(seconds);
  const payload = {
    timestamp,
    seconds,
    comment: commentText,
    triggerPrompt: louflixState.selectedPrompt || undefined,
  };
  louflixState.isSubmitting = true;
  if (elements.louflixCommentSubmit) elements.louflixCommentSubmit.disabled = true;
  setLouflixStatus("Enviando comentário…");
  try {
    const response = await fetch(`${API_BASE}/louflix/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Falha ao salvar comentário");
    const saved = await response.json();
    louflixState.session = louflixState.session || {};
    const nextComments = [...(louflixState.session.comments ?? []), saved];
    louflixState.session.comments = nextComments;
    renderLouflixComments(nextComments);
    elements.louflixCommentForm?.reset();
    louflixState.selectedTriggerIndex = null;
    louflixState.selectedPrompt = "";
    renderLouflixTriggers(louflixState.session.triggers ?? []);
    resetLouflixPromptPreview();
    setLouflixStatus("Comentário registrado.");
  } catch (error) {
    console.error("Falha ao enviar comentário para LouFlix", error);
    setLouflixStatus("Erro ao enviar comentário. Tente novamente.");
  } finally {
    louflixState.isSubmitting = false;
    if (elements.louflixCommentSubmit) elements.louflixCommentSubmit.disabled = false;
  }
}

function handleLouflixEscapeKey(event) {
  if (event.key === "Escape" && louflixState.isOpen) {
    closeLouflixPanel();
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
}

function closeContextPanel() {
  elements.contextOverlay?.classList.add("is-hidden");
  contextState.isOpen = false;
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
  }
  proactiveState.lastUserActivity = Date.now();
  startProactiveTimer();
}

function registerUserActivity() {
  refreshProactiveWatcher({ resetAttempts: true });
}

function queueLouReplyAfterUserMessage(serverId, channelId, referenceMessage) {
  if (!serverId || !channelId) return;
  cancelLouReplyTimer();
  cancelLouReplyRequest();
  interruptLouOutput();
  louReplyState.serverId = serverId;
  louReplyState.channelId = channelId;
  louReplyState.referenceMessage = referenceMessage;
  const waitMs = randomBetween(louReplyState.debounceRange.min, louReplyState.debounceRange.max);
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
  if (proactiveState.attempt >= proactiveState.maxAttempts) return;
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
  if (!manual && proactiveState.attempt >= proactiveState.maxAttempts) return;
  if (proactiveState.requestInFlight) return;
  proactiveState.requestInFlight = true;
  const requestStartedAt = Date.now();
  const targetInitialDelay = randomBetween(LOU_TYPING_INITIAL_DELAY.min, LOU_TYPING_INITIAL_DELAY.max);
  try {
    const message = await postJSON(`${API_BASE}/proactive`, {
      serverId: server.id,
      channelId: channel.id,
      attempt: proactiveState.attempt,
    });
    const elapsed = Date.now() - requestStartedAt;
    const remainingInitialWait = Math.max(targetInitialDelay - elapsed, 0);
    await playLouTypingSequence(server.id, channel.id, [message], { initialWait: remainingInitialWait });
    proactiveState.lastUserActivity = Date.now();
    if (manual) {
      proactiveState.attempt = Math.min(proactiveState.attempt + 1, proactiveState.maxAttempts);
    } else {
      proactiveState.attempt += 1;
    }
  } catch (error) {
    console.error("Falha ao gerar mensagem proativa", error);
  } finally {
    proactiveState.requestInFlight = false;
    if (proactiveState.attempt < proactiveState.maxAttempts) {
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
