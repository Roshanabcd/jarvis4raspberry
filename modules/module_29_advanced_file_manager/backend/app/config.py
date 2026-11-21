"""Configuration for JARVIS Module 29 — Advanced File Manager."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileManagerConfig:
    host: str = "0.0.0.0"
    port: int = 8129
    db_path: str = "./data/jarvis_file_manager.db"
    root_dir: str = "./data/managed_files"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "FileManagerConfig":
        return cls(
            host=os.getenv("JARVIS_M29_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M29_PORT", "8129")),
            db_path=os.getenv("JARVIS_M29_DB_PATH", "./data/jarvis_file_manager.db"),
            root_dir=os.getenv("JARVIS_M29_ROOT_DIR", "./data/managed_files"),
            cors_origins=os.getenv("JARVIS_M29_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.root_dir).mkdir(parents=True, exist_ok=True)
        (Path(self.root_dir) / "_trash").mkdir(parents=True, exist_ok=True)
