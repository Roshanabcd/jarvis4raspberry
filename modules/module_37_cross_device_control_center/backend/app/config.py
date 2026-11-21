"""Configuration for JARVIS Module 37 — Cross-Device Control Center."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DeviceMeshConfig:
    host: str = "0.0.0.0"
    port: int = 8137
    db_path: str = "./data/jarvis_devices.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "DeviceMeshConfig":
        return cls(
            host=os.getenv("JARVIS_M37_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M37_PORT", "8137")),
            db_path=os.getenv("JARVIS_M37_DB_PATH", "./data/jarvis_devices.db"),
            cors_origins=os.getenv("JARVIS_M37_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
