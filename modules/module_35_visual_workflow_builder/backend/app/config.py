"""Configuration for JARVIS Module 35 — Visual Workflow Builder."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkflowConfig:
    host: str = "0.0.0.0"
    port: int = 8135
    db_path: str = "./data/jarvis_workflows.db"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "WorkflowConfig":
        return cls(
            host=os.getenv("JARVIS_M35_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M35_PORT", "8135")),
            db_path=os.getenv("JARVIS_M35_DB_PATH", "./data/jarvis_workflows.db"),
            cors_origins=os.getenv("JARVIS_M35_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        db_parent = Path(self.db_path).parent
        if str(db_parent) not in ("", "."):
            db_parent.mkdir(parents=True, exist_ok=True)
