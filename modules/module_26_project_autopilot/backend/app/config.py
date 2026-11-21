"""Configuration for JARVIS Module 26 — Project Autopilot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectAutopilotConfig:
    host: str = "0.0.0.0"
    port: int = 8126
    db_path: str = "./data/jarvis_project_autopilot.db"
    workspace_root: str = "./data/workspaces"
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "ProjectAutopilotConfig":
        return cls(
            host=os.getenv("JARVIS_M26_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M26_PORT", "8126")),
            db_path=os.getenv("JARVIS_M26_DB_PATH", "./data/jarvis_project_autopilot.db"),
            workspace_root=os.getenv("JARVIS_M26_WORKSPACE_ROOT", "./data/workspaces"),
            cors_origins=os.getenv("JARVIS_M26_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.workspace_root).mkdir(parents=True, exist_ok=True)
