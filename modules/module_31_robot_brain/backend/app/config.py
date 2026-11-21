"""Configuration for JARVIS Module 31 — JARVIS Robot Brain."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RobotBrainConfig:
    host: str = "0.0.0.0"
    port: int = 8131
    db_path: str = "./data/jarvis_robot_brain.db"
    cors_origins: str = "*"
    max_linear_mps: float = 1.2
    max_angular_rps: float = 1.5
    min_obstacle_m: float = 0.35
    min_battery_pct: float = 15.0

    @classmethod
    def from_env(cls) -> "RobotBrainConfig":
        return cls(
            host=os.getenv("JARVIS_M31_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M31_PORT", "8131")),
            db_path=os.getenv("JARVIS_M31_DB_PATH", "./data/jarvis_robot_brain.db"),
            cors_origins=os.getenv("JARVIS_M31_CORS_ORIGINS", "*"),
            max_linear_mps=float(os.getenv("JARVIS_M31_MAX_LINEAR_MPS", "1.2")),
            max_angular_rps=float(os.getenv("JARVIS_M31_MAX_ANGULAR_RPS", "1.5")),
            min_obstacle_m=float(os.getenv("JARVIS_M31_MIN_OBSTACLE_M", "0.35")),
            min_battery_pct=float(os.getenv("JARVIS_M31_MIN_BATTERY_PCT", "15.0")),
        )

    def ensure_dirs(self) -> None:
        db_parent = Path(self.db_path).parent
        if str(db_parent) not in ("", "."):
            db_parent.mkdir(parents=True, exist_ok=True)
