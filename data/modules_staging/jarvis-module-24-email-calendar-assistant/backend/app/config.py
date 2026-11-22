"""Environment-driven configuration for JARVIS Module 24 — Email & Calendar Assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EmailCalendarConfig:
    host: str = "0.0.0.0"
    port: int = 8124
    db_path: str = "./data/jarvis_email_calendar.db"
    require_approval_for_send: bool = True
    workday_start_hour: int = 9
    workday_end_hour: int = 18
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "EmailCalendarConfig":
        return cls(
            host=os.getenv("JARVIS_M24_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M24_PORT", "8124")),
            db_path=os.getenv("JARVIS_M24_DB_PATH", "./data/jarvis_email_calendar.db"),
            require_approval_for_send=os.getenv("JARVIS_M24_REQUIRE_APPROVAL_SEND", "true").lower() in ("1", "true", "yes"),
            workday_start_hour=int(os.getenv("JARVIS_M24_WORKDAY_START", "9")),
            workday_end_hour=int(os.getenv("JARVIS_M24_WORKDAY_END", "18")),
            cors_origins=os.getenv("JARVIS_M24_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
