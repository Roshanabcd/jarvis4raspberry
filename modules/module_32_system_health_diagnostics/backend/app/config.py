"""Configuration for JARVIS Module 32 — System Health & Diagnostics."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SystemHealthConfig:
    host: str = "0.0.0.0"
    port: int = 8132
    db_path: str = "./data/jarvis_system_health.db"
    monitor_disk_path: str = "/"
    cors_origins: str = "*"
    probe_timeout_s: float = 0.5

    @classmethod
    def from_env(cls) -> "SystemHealthConfig":
        return cls(
            host=os.getenv("JARVIS_M32_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M32_PORT", "8132")),
            db_path=os.getenv("JARVIS_M32_DB_PATH", "./data/jarvis_system_health.db"),
            monitor_disk_path=os.getenv("JARVIS_M32_MONITOR_DISK_PATH", "/"),
            cors_origins=os.getenv("JARVIS_M32_CORS_ORIGINS", "*"),
            probe_timeout_s=float(os.getenv("JARVIS_M32_PROBE_TIMEOUT_S", "0.5")),
        )

    def ensure_dirs(self) -> None:
        db_parent = Path(self.db_path).parent
        if str(db_parent) not in ("", "."):
            db_parent.mkdir(parents=True, exist_ok=True)
