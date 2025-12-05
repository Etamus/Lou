"""Configuration helpers for the Lou shared service layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LouServiceConfig:
    """Collects filesystem paths consumed by LouService components."""

    root_dir: Path
    data_dir: Path
    assets_dir: Path
    avatars_dir: Path
    gifs_dir: Path
    chat_data_file: Path
    memory_file: Path
    short_term_file: Path
    style_file: Path
    personality_file: Path

    @classmethod
    def from_root(cls, root_dir: Path) -> "LouServiceConfig":
        root_dir = root_dir.resolve()
        data_dir = root_dir / "data"
        assets_dir = root_dir / "assets"
        avatars_dir = assets_dir / "avatars"
        gifs_dir = assets_dir / "gifs"
        chat_data_file = data_dir / "chat_data.json"
        memory_file = data_dir / "memory_bank.json"
        short_term_file = data_dir / "short_term_memory.json"
        style_file = data_dir / "style_bank.json"
        personality_file = data_dir / "personality_prompt.json"
        return cls(
            root_dir=root_dir,
            data_dir=data_dir,
            assets_dir=assets_dir,
            avatars_dir=avatars_dir,
            gifs_dir=gifs_dir,
            chat_data_file=chat_data_file,
            memory_file=memory_file,
            short_term_file=short_term_file,
            style_file=style_file,
            personality_file=personality_file,
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.avatars_dir.mkdir(parents=True, exist_ok=True)
        self.gifs_dir.mkdir(parents=True, exist_ok=True)
