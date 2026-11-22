"""Configuration for JARVIS Module 36 — Screen Vision Assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VisionConfig:
    host: str = "0.0.0.0"
    port: int = 8136
    db_path: str = "./data/jarvis_vision.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "VisionConfig":
        return cls(
            host=os.getenv("JARVIS_M36_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M36_PORT", "8136")),
            db_path=os.getenv("JARVIS_M36_DB_PATH", "./data/jarvis_vision.db"),
            cors_origins=os.getenv("JARVIS_M36_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
