"""Environment-driven configuration for JARVIS Module 20."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConversationalConfig:
    host: str = "0.0.0.0"
    port: int = 8120
    db_path: str = "./data/jarvis_conversational_ai.db"
    provider: str = "simulated_local"
    provider_url: str = ""
    provider_api_key: str = ""
    provider_model: str = "jarvis-local-sim-v1"
    context_window: int = 12
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "ConversationalConfig":
        return cls(
            host=os.getenv("JARVIS_M20_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M20_PORT", "8120")),
            db_path=os.getenv("JARVIS_M20_DB_PATH", "./data/jarvis_conversational_ai.db"),
            provider=os.getenv("JARVIS_M20_PROVIDER", "simulated_local"),
            provider_url=os.getenv("JARVIS_M20_PROVIDER_URL", ""),
            provider_api_key=os.getenv("JARVIS_M20_PROVIDER_API_KEY", ""),
            provider_model=os.getenv("JARVIS_M20_PROVIDER_MODEL", "jarvis-local-sim-v1"),
            context_window=max(2, min(50, int(os.getenv("JARVIS_M20_CONTEXT_WINDOW", "12")))),
            cors_origins=os.getenv("JARVIS_M20_CORS_ORIGINS", "*"),
        )

    def ensure_db_dir(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
