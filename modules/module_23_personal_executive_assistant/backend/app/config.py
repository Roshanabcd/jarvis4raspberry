"""Environment-driven configuration for JARVIS Module 23 — Personal Executive Assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutiveAssistantConfig:
    host: str = "0.0.0.0"
    port: int = 8123
    db_path: str = "./data/jarvis_executive_assistant.db"
    workday_start_hour: int = 9
    workday_end_hour: int = 18
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "ExecutiveAssistantConfig":
        return cls(
            host=os.getenv("JARVIS_M23_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M23_PORT", "8123")),
            db_path=os.getenv("JARVIS_M23_DB_PATH", "./data/jarvis_executive_assistant.db"),
            workday_start_hour=int(os.getenv("JARVIS_M23_WORKDAY_START", "9")),
            workday_end_hour=int(os.getenv("JARVIS_M23_WORKDAY_END", "18")),
            cors_origins=os.getenv("JARVIS_M23_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
