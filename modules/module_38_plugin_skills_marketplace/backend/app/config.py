"""Configuration for JARVIS Module 38 — Plugin & Skills Marketplace."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MarketplaceConfig:
    host: str = "0.0.0.0"
    port: int = 8138
    db_path: str = "./data/jarvis_marketplace.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "MarketplaceConfig":
        return cls(
            host=os.getenv("JARVIS_M38_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M38_PORT", "8138")),
            db_path=os.getenv("JARVIS_M38_DB_PATH", "./data/jarvis_marketplace.db"),
            cors_origins=os.getenv("JARVIS_M38_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
