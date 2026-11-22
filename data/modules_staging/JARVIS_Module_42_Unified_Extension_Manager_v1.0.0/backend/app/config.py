"""Configuration for JARVIS Module 42 — Unified Extension Manager."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExtensionManagerConfig:
    host: str = "0.0.0.0"
    port: int = 8142
    db_path: str = "./data/jarvis_extensions.db"
    default_archives_dir: str = "/home/roshan/Downloads/module-jarvis"
    max_uncompressed_bytes: int = 200 * 1024 * 1024  # 200 MiB
    max_compression_ratio: float = 100.0
    max_archive_files: int = 2500
    health_timeout_seconds: float = 3.0
    api_token: str = ""
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "ExtensionManagerConfig":
        return cls(
            host=os.getenv("JARVIS_M42_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M42_PORT", "8142")),
            db_path=os.getenv("JARVIS_M42_DB_PATH", "./data/jarvis_extensions.db"),
            default_archives_dir=os.getenv("JARVIS_M42_ARCHIVES_DIR", "/home/roshan/Downloads/module-jarvis"),
            max_uncompressed_bytes=max(1024, int(os.getenv("JARVIS_M42_MAX_UNCOMPRESSED_MB", "200")) * 1024 * 1024),
            max_compression_ratio=max(2.0, float(os.getenv("JARVIS_M42_MAX_COMPRESSION_RATIO", "100.0"))),
            max_archive_files=max(10, int(os.getenv("JARVIS_M42_MAX_ARCHIVE_FILES", "2500"))),
            health_timeout_seconds=max(0.2, float(os.getenv("JARVIS_M42_HEALTH_TIMEOUT", "3.0"))),
            api_token=os.getenv("JARVIS_M42_API_TOKEN", "").strip(),
            cors_origins=os.getenv("JARVIS_M42_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
