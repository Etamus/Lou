# Neve Migration Plan

This document tracks the remaining work required to reach feature parity between the legacy PySide6 client and the new Neve web frontend.

## Phase 1 – Core backend parity

1. **Server & channel management**
   - PATCH/DELETE endpoints for servers and channels (rename, avatar swap, deletion guard logic).
   - Update `LouService` with `update_server`, `delete_server`, `update_channel`, `delete_channel` helpers.
   - Extend data validation (prevent deleting last text channel, keep icon chars in sync).
2. **Profiles service**
   - API to read/update `user` and `model` profiles, mirroring the legacy `UserSettingsDialog` behavior.
   - Avatar file handling hooks so we can later support uploads or asset selection.
3. **Message metadata**
   - Persist reply snapshots (`is_reply_to` payload) and expose an endpoint to fetch a single message when building reply previews in the frontend.

## Phase 2 – Frontend feature port

1. **Discord-like modals**
   - Recreate the legacy dialogs (server settings, create server, create channel, confirmation) as reusable web components with matching layout/typography.
   - Add context menus for server/channel items to trigger rename/delete actions against the new endpoints.
2. **Reply workflow**
   - Message hover actions to start/cancel replies and display banners similar to `ReplyIndicatorWidget`.
   - Send `replyTo` metadata via the existing POST `/messages` endpoint.
3. **User profile drawer**
   - Implement the avatar/name editor that talks to the profiles API and updates the live sidebar card.

## Phase 3 – Advanced behaviors

1. **AI context + proactive flows**
   - Move `_handle_context_update`, memory/style banks, and proactive messaging loops from `LouBE/LouProactive` into backend jobs that the frontend can poll.
2. **Personality editor (LouEditor)**
   - Port `LouEditor.PersonalityEditorWindow` into uma tela web dedicada (já entregue como overlay editável) e seguir refinando a UX.
   - O antigo `LouFlix.MoviePlayerWindow` foi oficialmente descontinuado; em vez de portar o player, estamos limpando código/documentação para refletir a remoção.
3. **Assets management**
   - Allow uploading avatars/GIFs from o browser, store them under `assets/` e atualizar o cache do `LouService` sem reiniciar. (Fluxo completo de GIFs ✅ — overlay aceita upload direto, atualiza o catálogo e mostra o novo item; upload de avatares ✅ — perfis e servidores agora enviam PNG/JPG direto para `/api/avatars` e preenchem o campo automaticamente.)

_Atualização recente:_ o backend agora expõe o `LouAIResponder`, que recicla o prompt completo da personalidade e o contexto do `LouService` para gerar respostas reais via Gemini. O frontend chama o novo endpoint `/api/ai/reply`, mostra um placeholder de digitação e reporta erros amigáveis quando a variável `GEMINI_API_KEY` não está configurada.

We will iterate phase-by-phase, ensuring every backend addition immediately powers at least one frontend feature to keep the stack usable throughout the migration.

## Status board

| Feature | Legacy origin | Neve status |
| --- | --- | --- |
| Server rename/delete dialog | `ServerSettingsDialog` in `LouFE.py` | ✅ Modal with rename + delete parity (no avatar upload yet) |
| Channel rename/delete context menu | `LouBE.AppLogicMixin` + `LouFE` dialogs | ✅ Inline actions with dialogs hitting PATCH/DELETE APIs |
| Profile settings window | `UserSettingsDialog` | ✅ Tabbed modal with live preview; missing file picker/upload |
| Reply indicator & hover actions | `ReplyIndicatorWidget`, `_handle_reply_button_clicked` | ✅ Message hover action + reply banner replicating desktop flow |
| Personality editor | `LouEditor.PersonalityEditorWindow` | ✅ Overlay web editor com categorias, bind bidirecional e salvamento via /api/personality |
| Proactive/worker loops | `LouProactive`, `_handle_context_update` | ✅ Context API exposta + timer proativo com POST /api/proactive |
| Media windows (LouFlix) | `LouFlix.py`, `LouFlixWorker.py` | ❌ Funcionalidade descontinuada; player, timeline e APIs removidos do Neve |
| GIF picker / reactions | `LouFE` composer GIF dialog | ✅ Overlay web lista assets/gifs, permite busca, envia anexos e agora faz upload com refresh automático |
| Gemini chat replies | `LouIAFE`, `LouBE` | ✅ `/api/ai/reply` usa `LouAIResponder` (Gemini) com contexto compartilhado; frontend mostra indicador "digitando" e feedback de erro |
