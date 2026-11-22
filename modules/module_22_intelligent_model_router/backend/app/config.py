"""Environment-driven configuration for JARVIS Module 22 — Intelligent AI Model Router."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelRouterConfig:
    host: str = "0.0.0.0"
    port: int = 8122
    db_path: str = "./data/jarvis_model_router.db"
    adapter_mode: str = "simulated"
    circuit_breaker_threshold: int = 2
    default_daily_budget_usd: float = 5.00
    enable_cache: bool = True
    cors_origins: str = "*"

    @classmethod
    def from_env(cls) -> "ModelRouterConfig":
        return cls(
            host=os.getenv("JARVIS_M22_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M22_PORT", "8122")),
            db_path=os.getenv("JARVIS_M22_DB_PATH", "./data/jarvis_model_router.db"),
            adapter_mode=os.getenv("JARVIS_M22_ADAPTER_MODE", "simulated"),
            circuit_breaker_threshold=int(os.getenv("JARVIS_M22_CB_THRESHOLD", "2")),
            default_daily_budget_usd=float(os.getenv("JARVIS_M22_DAILY_BUDGET_USD", "5.00")),
            enable_cache=os.getenv("JARVIS_M22_ENABLE_CACHE", "true").lower() in ("1", "true", "yes"),
            cors_origins=os.getenv("JARVIS_M22_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
