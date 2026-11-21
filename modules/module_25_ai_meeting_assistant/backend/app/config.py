"""Environment-driven configuration for JARVIS Module 25 — AI Meeting Assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MeetingAssistantConfig:
    host: str = "0.0.0.0"
    port: int = 8125
    db_path: str = "./data/jarvis_meeting_assistant.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "MeetingAssistantConfig":
        return cls(
            host=os.getenv("JARVIS_M25_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M25_PORT", "8125")),
            db_path=os.getenv("JARVIS_M25_DB_PATH", "./data/jarvis_meeting_assistant.db"),
            cors_origins=os.getenv("JARVIS_M25_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
