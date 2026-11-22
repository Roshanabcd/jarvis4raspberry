"""Configuration for JARVIS Module 33 — Defensive Cybersecurity Agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CyberSecurityConfig:
    host: str = "0.0.0.0"
    port: int = 8133
    db_path: str = "./data/jarvis_cybersecurity.db"
    scan_root: str = "./sandbox_target"
    cors_origins: str = "*"
    brute_force_threshold: int = 3

    @classmethod
    def from_env(cls) -> "CyberSecurityConfig":
        return cls(
            host=os.getenv("JARVIS_M33_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M33_PORT", "8133")),
            db_path=os.getenv("JARVIS_M33_DB_PATH", "./data/jarvis_cybersecurity.db"),
            scan_root=os.getenv("JARVIS_M33_SCAN_ROOT", "./sandbox_target"),
            cors_origins=os.getenv("JARVIS_M33_CORS_ORIGINS", "*"),
            brute_force_threshold=int(os.getenv("JARVIS_M33_BRUTE_FORCE_THRESHOLD", "3")),
        )

    def ensure_dirs(self) -> None:
        db_parent = Path(self.db_path).parent
        if str(db_parent) not in ("", "."):
            db_parent.mkdir(parents=True, exist_ok=True)
        Path(self.scan_root).mkdir(parents=True, exist_ok=True)
