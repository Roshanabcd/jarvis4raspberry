"""Configuration for JARVIS Module 43 — Autonomous Screen Guardian."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


PROTECTED_SYSTEM_PATHS = {
    "/",
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/boot",
    "/root",
    "/var",
    "/sys",
    "/proc",
    "/dev",
}


@dataclass
class ScreenGuardianConfig:
    host: str = "0.0.0.0"
    port: int = 8143
    db_path: str = "./data/jarvis_screen_guardian.db"
    capture_interval_sec: float = 2.0
    max_inference_concurrency: int = 2
    store_raw_screenshots: bool = False
    allow_remote_vision_upload: bool = False
    auto_start_on_boot: bool = False
    trusted_workspaces: List[str] = field(default_factory=list)
    vision_provider: str = "none"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    api_token: str = ""
    cors_origins: str = "*"
    max_repair_timeout_sec: float = 60.0
    performance_mode: str = "pi5_balanced"  # pi5_eco | pi5_balanced | performance

    @classmethod
    def from_env(cls) -> "ScreenGuardianConfig":
        raw_ws = os.getenv("JARVIS_M43_TRUSTED_WORKSPACES", "")
        workspaces = [str(Path(p.strip()).expanduser().resolve()) for p in raw_ws.split(",") if p.strip()]
        return cls(
            host=os.getenv("JARVIS_M43_HOST", "0.0.0.0"),
            port=int(os.getenv("JARVIS_M43_PORT", "8143")),
            db_path=os.getenv("JARVIS_M43_DB_PATH", "./data/jarvis_screen_guardian.db"),
            capture_interval_sec=max(0.5, float(os.getenv("JARVIS_M43_CAPTURE_INTERVAL_SEC", "2.0"))),
            max_inference_concurrency=max(1, min(4, int(os.getenv("JARVIS_M43_MAX_INFERENCE_CONCURRENCY", "2")))),
            store_raw_screenshots=_env_bool("JARVIS_M43_STORE_RAW_SCREENSHOTS", False),
            allow_remote_vision_upload=_env_bool("JARVIS_M43_ALLOW_REMOTE_VISION_UPLOAD", False),
            auto_start_on_boot=_env_bool("JARVIS_M43_AUTO_START_ON_BOOT", False),
            trusted_workspaces=workspaces,
            vision_provider=os.getenv("JARVIS_M43_VISION_PROVIDER", "none").strip().lower(),
            gemini_api_key=os.getenv("JARVIS_M43_GEMINI_API_KEY", "").strip(),
            openai_api_key=os.getenv("JARVIS_M43_OPENAI_API_KEY", "").strip(),
            api_token=os.getenv("JARVIS_M43_API_TOKEN", "").strip(),
            cors_origins=os.getenv("JARVIS_M43_CORS_ORIGINS", "*"),
        )

    def ensure_dirs(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
