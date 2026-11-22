"""Configuration for JARVIS Module 30 — Smart Home Controller."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SmartHomeConfig:
    host: str = "0.0.0.0"
    port: int = 8130
    db_path: str = "./data/jarvis_smart_home.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "SmartHomeConfig":
        return cls(
            host=os.getenv("JARVIS_M30_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M30_PORT", "8130")),
            db_path=os.getenv("JARVIS_M30_DB_PATH", "./data/jarvis_smart_home.db"),
            cors_origins=os.getenv("JARVIS_M30_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
