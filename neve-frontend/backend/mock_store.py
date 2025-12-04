"""Simple JSON-backed store for the Neve frontend mock backend."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


@dataclass
class MessagePayload:
    server_id: str
    channel_id: str
    author_id: str
    content: str
    reply_to: Optional[str] = None


class MockStore:
    """Persists chat data in a JSON file so the frontend can remain stateful."""

    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path
        self._lock = threading.Lock()
        self._data = self._load_or_seed()

    def _load_or_seed(self) -> Dict[str, Any]:
        if not self._data_path.exists():
            raise FileNotFoundError(f"Mock data file not found: {self._data_path}")
        with self._data_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _persist(self) -> None:
        with self._data_path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2, ensure_ascii=False)

    # --- Query helpers -------------------------------------------------

    def get_profiles(self) -> Dict[str, Any]:
        return self._data.get("profiles", {})

    def get_servers(self) -> List[Dict[str, Any]]:
        return self._data.get("servers", [])

    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        return next((srv for srv in self.get_servers() if srv["id"] == server_id), None)

    def get_channel(self, server_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        server = self.get_server(server_id)
        if not server:
            return None
        return next((chn for chn in server.get("channels", []) if chn["id"] == channel_id), None)

    def get_channel_messages(self, server_id: str, channel_id: str) -> List[Dict[str, Any]]:
        channel = self.get_channel(server_id, channel_id)
        return channel.get("messages", []) if channel else []

    # --- Mutations -----------------------------------------------------

    def add_message(self, payload: MessagePayload) -> Dict[str, Any]:
        with self._lock:
            channel = self.get_channel(payload.server_id, payload.channel_id)
            if channel is None:
                raise KeyError("Canal nao encontrado")
            message = self._build_message(payload)
            channel.setdefault("messages", []).append(message)
            self._persist()
            return message

    # --- Internal helpers ----------------------------------------------

    def _build_message(self, payload: MessagePayload) -> Dict[str, Any]:
        message_id = f"m-{uuid.uuid4()}"
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        message = {
            "id": message_id,
            "authorId": payload.author_id,
            "content": payload.content,
            "timestamp": timestamp,
        }
        if payload.reply_to:
            message["replyTo"] = payload.reply_to
        return message


__all__ = ["MockStore", "MessagePayload"]
