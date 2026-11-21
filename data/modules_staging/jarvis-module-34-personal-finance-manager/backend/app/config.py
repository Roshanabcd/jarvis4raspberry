"""Configuration for JARVIS Module 34 — Personal Finance Manager."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FinanceConfig:
    host: str = "0.0.0.0"
    port: int = 8134
    db_path: str = "./data/jarvis_finance.db"
    default_currency: str = "USD"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "FinanceConfig":
        return cls(
            host=os.getenv("JARVIS_M34_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M34_PORT", "8134")),
            db_path=os.getenv("JARVIS_M34_DB_PATH", "./data/jarvis_finance.db"),
            default_currency=os.getenv("JARVIS_M34_DEFAULT_CURRENCY", "USD"),
            cors_origins=os.getenv("JARVIS_M34_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        db_parent = Path(self.db_path).parent
        if str(db_parent) not in ("", "."):
            db_parent.mkdir(parents=True, exist_ok=True)
