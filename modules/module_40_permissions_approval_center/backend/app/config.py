"""Configuration for JARVIS Module 40 — Permissions & Approval Center."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ApprovalConfig:
    host: str = "0.0.0.0"
    port: int = 8140
    db_path: str = "./data/jarvis_approvals.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "ApprovalConfig":
        return cls(
            host=os.getenv("JARVIS_M40_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M40_PORT", "8140")),
            db_path=os.getenv("JARVIS_M40_DB_PATH", "./data/jarvis_approvals.db"),
            cors_origins=os.getenv("JARVIS_M40_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
