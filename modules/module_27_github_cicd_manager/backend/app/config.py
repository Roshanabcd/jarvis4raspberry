"""Configuration for JARVIS Module 27 — GitHub & CI/CD Manager."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitHubCICDConfig:
    host: str = "0.0.0.0"
    port: int = 8127
    db_path: str = "./data/jarvis_github_cicd.db"
    cors_origins: str = "*"
    webhook_secret: str = "local-dev-webhook-secret"

    @classmethod
    def from_env(cls) -> "GitHubCICDConfig":
        return cls(
            host=os.getenv("JARVIS_M27_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M27_PORT", "8127")),
            db_path=os.getenv("JARVIS_M27_DB_PATH", "./data/jarvis_github_cicd.db"),
            cors_origins=os.getenv("JARVIS_M27_CORS_ORIGINS", "*"),
            webhook_secret=os.getenv("JARVIS_M27_WEBHOOK_SECRET", "local-dev-webhook-secret"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
