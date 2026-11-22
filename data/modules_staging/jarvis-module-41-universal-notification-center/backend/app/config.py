"""Configuration for JARVIS Module 41 — Universal Notification Center."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NotificationConfig:
    host: str = "0.0.0.0"
    port: int = 8141
    db_path: str = "./data/jarvis_notifications.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "NotificationConfig":
        return cls(
            host=os.getenv("JARVIS_M41_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M41_PORT", "8141")),
            db_path=os.getenv("JARVIS_M41_DB_PATH", "./data/jarvis_notifications.db"),
            cors_origins=os.getenv("JARVIS_M41_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
