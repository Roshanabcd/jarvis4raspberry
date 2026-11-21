"""Configuration for JARVIS Module 39 — Backup & Recovery Manager."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BackupConfig:
    host: str = "0.0.0.0"
    port: int = 8139
    db_path: str = "./data/jarvis_backups.db"
    sandbox_root: str = "./data/workspace"
    archive_dir: str = "./data/archives"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "BackupConfig":
        return cls(
            host=os.getenv("JARVIS_M39_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M39_PORT", "8139")),
            db_path=os.getenv("JARVIS_M39_DB_PATH", "./data/jarvis_backups.db"),
            sandbox_root=os.getenv("JARVIS_M39_SANDBOX_ROOT", "./data/workspace"),
            archive_dir=os.getenv("JARVIS_M39_ARCHIVE_DIR", "./data/archives"),
            cors_origins=os.getenv("JARVIS_M39_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        Path(self.sandbox_root).expanduser().resolve().mkdir(parents=True, exist_ok=True)
        Path(self.archive_dir).expanduser().resolve().mkdir(parents=True, exist_ok=True)
