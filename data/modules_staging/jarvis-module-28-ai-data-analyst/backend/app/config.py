"""Configuration for JARVIS Module 28 — AI Data Analyst."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DataAnalystConfig:
    host: str = "0.0.0.0"
    port: int = 8128
    db_path: str = "./data/jarvis_ai_data_analyst.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "DataAnalystConfig":
        return cls(
            host=os.getenv("JARVIS_M28_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M28_PORT", "8128")),
            db_path=os.getenv("JARVIS_M28_DB_PATH", "./data/jarvis_ai_data_analyst.db"),
            cors_origins=os.getenv("JARVIS_M28_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
