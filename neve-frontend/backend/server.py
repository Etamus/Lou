"""Local HTTP server that powers the Neve experimental frontend."""

from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import base64
import binascii
import json
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse
import uuid

from lou_service import LouService, LouServiceConfig, LouAIResponder

try:  # Optional user overrides
    from . import settings as neve_settings
except ImportError:  # pragma: no cover - optional module
    neve_settings = None
from lou_service.service import CreateMessagePayload

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "neve-frontend"
ASSETS_DIR = ROOT_DIR / "assets"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


def build_handler(service: LouService, ai_responder: Optional[LouAIResponder] = None) -> Callable[..., SimpleHTTPRequestHandler]:
    """Factory that wires the store into the HTTP handler."""

    class NeveRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

        # --- Primary routing -------------------------------------------------

        def do_GET(self) -> None:  # noqa: N802 (http signature)
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                self._handle_api_get(parsed.path)
                return
            if parsed.path.startswith("/assets/"):
                self._serve_asset(parsed.path)
                return
            if parsed.path in {"", "/"}:
                self.path = "/neve-frontend/index.html"
            super().do_GET()

        def do_POST(self) -> None:  # noqa: N802 (http signature)
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/api/"):
                self.send_error(404, "Endpoint nao encontrado")
                return
            self._handle_api_post(parsed.path)

        def do_PATCH(self) -> None:  # noqa: N802 (http signature)
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/api/"):
                self.send_error(404, "Endpoint nao encontrado")
                return
            self._handle_api_patch(parsed.path)

        def do_DELETE(self) -> None:  # noqa: N802 (http signature)
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/api/"):
                self.send_error(404, "Endpoint nao encontrado")
                return
            self._handle_api_delete(parsed.path)

        def do_OPTIONS(self) -> None:  # noqa: N802 (http signature)
            self.send_response(204)
            self._apply_cors_headers()
            self.end_headers()

        # --- API handlers ----------------------------------------------------

        def _handle_api_get(self, path: str) -> None:
            if path == "/api/bootstrap":
                payload = {"profiles": service.get_profiles(), "servers": service.list_servers()}
                self._json_response(payload)
                return
            if path == "/api/profiles":
                self._json_response(service.get_profiles())
                return
            if path == "/api/context":
                self._json_response(service.get_context_snapshot())
                return
            if path == "/api/gifs":
                self._json_response(service.get_available_gifs())
                return
            if path == "/api/personality":
                self._json_response(service.get_personality_prompt())
                return
            if path == "/api/media/videos":
                self._handle_list_videos()
                return

            parts = path.strip("/").split("/")
            if len(parts) >= 2 and parts[1] == "servers":
                if len(parts) == 2:
                    self._json_response(service.list_servers())
                    return
                server_id = parts[2]
                if len(parts) == 3:
                    server = service.get_server(server_id)
                    if server is None:
                        self.send_error(404, "Servidor nao encontrado")
                        return
                    self._json_response(server)
                    return
                if len(parts) >= 4 and parts[3] == "channels":
                    if len(parts) == 4:
                        channels = service.list_channels(server_id)
                        self._json_response(channels)
                        return
                    if len(parts) >= 6 and parts[5] == "messages":
                        channel_id = parts[4]
                        messages = service.list_messages(server_id, channel_id)
                        self._json_response(messages)
                        return

            self.send_error(404, "API nao encontrada")

        def _handle_api_post(self, path: str) -> None:
            parts = path.strip("/").split("/")
            if path == "/api/context":
                self._handle_update_context()
                return
            if path == "/api/proactive":
                self._handle_proactive_message()
                return
            if path == "/api/gifs":
                self._handle_upload_gif()
                return
            if path == "/api/avatars":
                self._handle_upload_avatar()
                return
            if path == "/api/ai/reply":
                self._handle_ai_reply()
                return
            if parts[:2] == ["api", "servers"]:
                if len(parts) == 2:
                    self._handle_create_server()
                    return
                if len(parts) >= 4 and parts[3] == "channels":
                    if len(parts) == 4:
                        self._handle_create_channel(parts[2])
                        return
                    if len(parts) >= 6 and parts[5] == "messages":
                        self._handle_create_message(parts[2], parts[4])
                        return

            self.send_error(404, "API nao encontrada")

        def _handle_api_patch(self, path: str) -> None:
            parts = path.strip("/").split("/")
            if path == "/api/personality":
                self._handle_update_personality()
                return
            if parts[:2] == ["api", "servers"] and len(parts) >= 3:
                server_id = parts[2]
                if len(parts) == 3:
                    self._handle_update_server(server_id)
                    return
                if len(parts) >= 5 and parts[3] == "channels":
                    channel_id = parts[4]
                    self._handle_update_channel(server_id, channel_id)
                    return
            if parts[:2] == ["api", "profiles"] and len(parts) == 3:
                self._handle_update_profile(parts[2])
                return
            self.send_error(404, "API nao encontrada")

        def _handle_api_delete(self, path: str) -> None:
            parts = path.strip("/").split("/")
            if parts[:2] == ["api", "servers"] and len(parts) >= 3:
                server_id = parts[2]
                if len(parts) == 3:
                    self._handle_delete_server(server_id)
                    return
                if len(parts) >= 5 and parts[3] == "channels":
                    channel_id = parts[4]
                    self._handle_delete_channel(server_id, channel_id)
                    return
            self.send_error(404, "API nao encontrada")

        def _handle_create_server(self) -> None:
            body = self._read_json_body()
            if body is None:
                return
            name = body.get("name", "").strip()
            if not name:
                self.send_error(400, "Nome obrigatorio")
                return
            try:
                server = service.create_server(name)
            except ValueError as exc:
                self.send_error(403, str(exc))
                return
            self._json_response(server, status=201)

        def _handle_create_channel(self, server_id: str) -> None:
            body = self._read_json_body()
            if body is None:
                return
            name = body.get("name", "").strip()
            if not name:
                self.send_error(400, "Nome obrigatorio")
                return
            try:
                channel = service.create_channel(server_id, name)
            except KeyError as exc:
                self.send_error(404, str(exc))
                return
            self._json_response(channel, status=201)

        def _handle_create_message(self, server_id: str, channel_id: str) -> None:
            body = self._read_json_body()
            if body is None:
                return
            required = {"authorId", "content"}
            if not required.issubset(body):
                self.send_error(400, "Campos obrigatorios ausentes")
                return
            payload = CreateMessagePayload(
                server_id=server_id,
                channel_id=channel_id,
                author_id=body["authorId"],
                content=body["content"],
                reply_to=body.get("replyTo"),
                attachments=body.get("attachments"),
            )
            try:
                message = service.add_message(payload)
            except KeyError as exc:
                self.send_error(404, str(exc))
                return
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            self._json_response(message, status=201)

        def _handle_upload_gif(self) -> None:
            body = self._read_json_body()
            if body is None:
                return
            raw_filename = (body.get("filename") or "").strip()
            if not raw_filename:
                self.send_error(400, "filename obrigatorio")
                return
            safe_filename = Path(raw_filename).name
            if not safe_filename.lower().endswith(".gif"):
                self.send_error(400, "Extensao permitida: .gif")
                return
            data_field = body.get("data")
            if not isinstance(data_field, str) or not data_field.strip():
                self.send_error(400, "Conteudo do arquivo obrigatorio")
                return
            payload_str = data_field.strip()
            if "," in payload_str:
                payload_str = payload_str.split(",", 1)[1]
            try:
                gif_bytes = base64.b64decode(payload_str)
            except (binascii.Error, ValueError):
                self.send_error(400, "Base64 invalido")
                return
            max_size = 5 * 1024 * 1024  # 5MB
            if len(gif_bytes) > max_size:
                self.send_error(400, "Arquivo acima de 5MB")
                return
            target_path = service.config.gifs_dir / safe_filename
            service.config.gifs_dir.mkdir(parents=True, exist_ok=True)
            with target_path.open("wb") as handle:
                handle.write(gif_bytes)
            gif_entries = service.refresh_gif_cache()
            self._json_response({"status": "ok", "filename": safe_filename, "gifs": gif_entries}, status=201)

        def _handle_upload_avatar(self) -> None:
            body = self._read_json_body()
            if body is None:
                return
            raw_filename = (body.get("filename") or "").strip()
            if not raw_filename:
                self.send_error(400, "filename obrigatorio")
                return
            data_field = body.get("data")
            if not isinstance(data_field, str) or not data_field.strip():
                self.send_error(400, "Conteudo do arquivo obrigatorio")
                return
            payload_str = data_field.strip()
            if "," in payload_str:
                payload_str = payload_str.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(payload_str)
            except (binascii.Error, ValueError):
                self.send_error(400, "Base64 invalido")
                return
            max_size = 2 * 1024 * 1024  # 2MB
            if len(image_bytes) > max_size:
                self.send_error(400, "Arquivo acima de 2MB")
                return
            safe_name = Path(raw_filename).name
            ext = safe_name.split(".")[-1].lower() if "." in safe_name else ""
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            if ext not in allowed_ext:
                self.send_error(400, "Extensoes permitidas: png, jpg, jpeg, gif, webp")
                return
            unique_name = f"avatar_{uuid.uuid4().hex}.{ext}"
            target_path = service.config.avatars_dir / unique_name
            service.config.avatars_dir.mkdir(parents=True, exist_ok=True)
            with target_path.open("wb") as handle:
                handle.write(image_bytes)
            payload = {
                "status": "ok",
                "filename": unique_name,
                "path": f"/assets/avatars/{unique_name}",
            }
            self._json_response(payload, status=201)

        def _handle_update_server(self, server_id: str) -> None:
            body = self._read_json_body()
            if body is None:
                return
            if "name" not in body:
                self.send_error(400, "Nome obrigatorio")
                return
            try:
                server = service.update_server(server_id, name=body.get("name"))
            except KeyError as exc:
                self.send_error(404, str(exc))
                return
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            self._json_response(server)

        def _handle_delete_server(self, server_id: str) -> None:
            try:
                service.delete_server(server_id)
            except (KeyError, ValueError) as exc:
                self.send_error(403, str(exc))
                return
            self._json_response({"status": "ok"})

        def _handle_update_channel(self, server_id: str, channel_id: str) -> None:
            body = self._read_json_body()
            if body is None:
                return
            if "name" not in body:
                self.send_error(400, "Nome obrigatorio")
                return
            try:
                channel = service.update_channel(server_id, channel_id, name=body["name"])
            except KeyError as exc:
                self.send_error(404, str(exc))
                return
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            self._json_response(channel)

        def _handle_delete_channel(self, server_id: str, channel_id: str) -> None:
            try:
                service.delete_channel(server_id, channel_id)
            except KeyError as exc:
                self.send_error(404, str(exc))
                return
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            self._json_response({"status": "ok"})

        def _handle_list_videos(self) -> None:
            videos_dir = ASSETS_DIR / "videos"
            entries = []
            if videos_dir.exists() and videos_dir.is_dir():
                for file_path in sorted(videos_dir.iterdir()):
                    if not file_path.is_file():
                        continue
                    if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
                        continue
                    entries.append(
                        {
                            "filename": file_path.name,
                            "path": f"/assets/videos/{file_path.name}",
                            "size": file_path.stat().st_size,
                        }
                    )
            self._json_response({"videos": entries})

        def _handle_update_profile(self, profile_key: str) -> None:
            body = self._read_json_body()
            if body is None:
                return
            if not any(key in body for key in ("name", "avatar")):
                self.send_error(400, "Nenhum campo para atualizar")
                return
            try:
                profile = service.update_profile(profile_key, name=body.get("name"), avatar=body.get("avatar"))
            except KeyError as exc:
                self.send_error(404, str(exc))
                return
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            self._json_response(profile)

        def _handle_update_personality(self) -> None:
            body = self._read_json_body()
            if body is None:
                return
            if not any(key in body for key in ("personality_definition", "technical_rules")):
                self.send_error(400, "Nenhum campo para atualizar")
                return
            try:
                payload = service.update_personality(
                    personality_definition=body.get("personality_definition"),
                    technical_rules=body.get("technical_rules"),
                )
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            self._json_response(payload)

        def _handle_update_context(self) -> None:
            body = self._read_json_body()
            if body is None:
                return
            long_term = body.get("long_term")
            short_term = body.get("short_term")
            styles = body.get("styles")
            if not any([long_term, short_term, styles]):
                self.send_error(400, "Nenhum campo para atualizar")
                return
            try:
                snapshot = service.update_context(long_term=long_term, short_term=short_term, styles=styles)
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            self._json_response(snapshot)

        def _handle_proactive_message(self) -> None:
            body = self._read_json_body()
            if body is None:
                return
            server_id = body.get("serverId")
            channel_id = body.get("channelId")
            attempt = int(body.get("attempt", 0))
            if not server_id or not channel_id:
                self.send_error(400, "serverId e channelId sao obrigatorios")
                return
            try:
                if ai_responder is not None:
                    message = ai_responder.generate_proactive_message(server_id, channel_id, attempt)
                else:
                    message = service.generate_proactive_message(server_id, channel_id, attempt=attempt)
            except KeyError as exc:
                self.send_error(404, str(exc))
                return
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            except RuntimeError as exc:
                self.send_error(503, str(exc))
                return
            except Exception as exc:  # pragma: no cover - guardrails only
                self.send_error(500, f"Falha ao gerar mensagem proativa: {exc}")
                return
            self._json_response(message, status=201)

        def _handle_ai_reply(self) -> None:
            if ai_responder is None:
                self.send_error(503, "IA desativada neste servidor")
                return
            body = self._read_json_body()
            if body is None:
                return
            server_id = (body.get("serverId") or "").strip()
            channel_id = (body.get("channelId") or "").strip()
            reply_to = (body.get("replyTo") or "").strip() or None
            if not server_id or not channel_id:
                self.send_error(400, "serverId e channelId sao obrigatorios")
                return
            try:
                ai_payload = ai_responder.generate_reply(server_id, channel_id, reply_to=reply_to)
            except KeyError as exc:
                self.send_error(404, str(exc))
                return
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            except RuntimeError as exc:
                self.send_error(503, str(exc))
                return
            except Exception as exc:  # pragma: no cover - guardrails only
                self.send_error(500, f"Falha ao gerar resposta: {exc}")
                return
            payload = {"messages": ai_payload.messages, "reasoning": ai_payload.reasoning}
            self._json_response(payload, status=201)

        def _read_json_body(self) -> Optional[dict[str, Any]]:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            try:
                return json.loads(raw_body or b"{}")
            except json.JSONDecodeError:
                self.send_error(400, "JSON invalido")
                return None

        # --- Static helpers --------------------------------------------------

        def _serve_asset(self, path: str) -> None:
            asset_path = ASSETS_DIR / path.replace("/assets/", "", 1)
            if not asset_path.exists() or not asset_path.is_file():
                self.send_error(404, "Asset nao encontrado")
                return
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(str(asset_path)))
            self.send_header("Content-Length", str(asset_path.stat().st_size))
            self._apply_cors_headers()
            self.end_headers()
            with asset_path.open("rb") as handle:
                self.wfile.write(handle.read())

        # --- Response helpers ------------------------------------------------

        def _json_response(self, payload: Any, *, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._apply_cors_headers()
            self.end_headers()
            self.wfile.write(body)

        def _apply_cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,PATCH,DELETE,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        # --- Logging ---------------------------------------------------------

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 (match base signature)
            # Silence default stdout noise; hook here if you need logs.
            return

    return NeveRequestHandler


def _resolve_api_key(override: Optional[str] = None) -> Optional[str]:
    if override:
        return override
    if neve_settings and getattr(neve_settings, "GEMINI_API_KEY", None):
        return neve_settings.GEMINI_API_KEY
    return None


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, *, api_key: Optional[str] = None) -> ThreadingHTTPServer:
    service = LouService(LouServiceConfig.from_root(ROOT_DIR))
    configured_key = _resolve_api_key(api_key)
    ai_responder = LouAIResponder(service, api_key=configured_key)
    handler = build_handler(service, ai_responder)
    httpd = ThreadingHTTPServer((host, port), handler)
    return httpd


def serve_forever(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = create_server(host, port)
    print(f"Neve backend escutando em http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve_forever()
