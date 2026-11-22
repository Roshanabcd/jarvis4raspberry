"""Environment-driven configuration for JARVIS Module 21."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BrowserAgentConfig:
    host: str = "0.0.0.0"
    port: int = 8121
    db_path: str = "./data/jarvis_browser_agent.db"
    downloads_dir: str = "./data/downloads"
    adapter_mode: str = "safe_simulated"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "BrowserAgentConfig":
        return cls(
            host=os.getenv("JARVIS_M21_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M21_PORT", "8121")),
            db_path=os.getenv("JARVIS_M21_DB_PATH", "./data/jarvis_browser_agent.db"),
            downloads_dir=os.getenv("JARVIS_M21_DOWNLOADS_DIR", "./data/downloads"),
            adapter_mode=os.getenv("JARVIS_M21_ADAPTER_MODE", "safe_simulated"),
            cors_origins=os.getenv("JARVIS_M21_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.downloads_dir).mkdir(parents=True, exist_ok=True)
