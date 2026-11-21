"""Environment-driven configuration for JARVIS Module 19."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ComputerAssistantConfig:
    host: str = "0.0.0.0"
    port: int = 8119
    db_path: str = "./data/jarvis_computer_assistant.db"
    sandbox_dir: str = "./data/sandbox_files"
    adapter_mode: str = "safe_demo"
    dry_run_default: bool = False
    cors_origins: str = "*"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "ComputerAssistantConfig":
        return cls(
            host=os.getenv("JARVIS_M19_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M19_PORT", "8119")),
            db_path=os.getenv("JARVIS_M19_DB_PATH", "./data/jarvis_computer_assistant.db"),
            sandbox_dir=os.getenv("JARVIS_M19_SANDBOX_DIR", "./data/sandbox_files"),
            adapter_mode=os.getenv("JARVIS_M19_ADAPTER_MODE", "safe_demo"),
            dry_run_default=os.getenv("JARVIS_M19_DRY_RUN_DEFAULT", "false").lower() in ("1", "true", "yes"),
            cors_origins=os.getenv("JARVIS_M19_CORS_ORIGINS", "*"),
            log_level=os.getenv("JARVIS_M19_LOG_LEVEL", "INFO"),
        )

    def ensure_dirs(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.sandbox_dir).mkdir(parents=True, exist_ok=True)
