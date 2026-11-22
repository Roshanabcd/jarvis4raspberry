"""Environment-driven configuration for JARVIS Module 18."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OrchestratorConfig:
    host: str = "0.0.0.0"
    port: int = 8118
    db_path: str = "./data/jarvis_orchestrator.db"
    max_concurrency: int = 4
    default_timeout_sec: float = 30.0
    poll_interval_sec: float = 0.08
    simulation_mode: bool = True
    cors_origins: str = "*"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        return cls(
            host=os.getenv("JARVIS_M18_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M18_PORT", "8118")),
            db_path=os.getenv("JARVIS_M18_DB_PATH", "./data/jarvis_orchestrator.db"),
            max_concurrency=max(1, min(32, int(os.getenv("JARVIS_M18_MAX_CONCURRENCY", "4")))),
            default_timeout_sec=max(1.0, float(os.getenv("JARVIS_M18_DEFAULT_TIMEOUT_SEC", "30.0"))),
            poll_interval_sec=max(0.02, float(os.getenv("JARVIS_M18_POLL_INTERVAL_SEC", "0.08"))),
            simulation_mode=os.getenv("JARVIS_M18_SIMULATION_MODE", "true").lower() in ("1", "true", "yes"),
            cors_origins=os.getenv("JARVIS_M18_CORS_ORIGINS", "*"),
            log_level=os.getenv("JARVIS_M18_LOG_LEVEL", "INFO"),
        )

    def ensure_db_dir(self) -> Path:
        p = Path(self.db_path)
        if str(p) != ":memory:":
            p.parent.mkdir(parents=True, exist_ok=True)
        return p
