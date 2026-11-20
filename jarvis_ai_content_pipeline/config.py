"""Environment-driven configuration for JARVIS AI Content Creation Pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_CONTENT_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_content_pipeline" / "content_pipeline.db").resolve()


@dataclass(frozen=True)
class ContentPipelineConfig:
    """Immutable runtime configuration for AI Content Creation Pipeline."""

    db_path: Path = field(default_factory=_default_db_path)

    provider: str = field(
        default_factory=lambda: os.getenv("JARVIS_CONTENT_PROVIDER", "auto").strip().lower()
    )
    openrouter_api_key: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "").strip()
    )
    openrouter_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
        ).strip()
    )
    openrouter_model: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
    )

    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2:3b").strip()
    )

    request_timeout_sec: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_CONTENT_TIMEOUT_SEC", "45"))
    )

    def active_provider_label(self) -> str:
        if self.provider == "offline":
            return "offline-template"
        if self.provider == "ollama":
            return f"ollama ({self.ollama_model})"
        if self.provider == "openrouter":
            if self.openrouter_api_key:
                return f"openrouter ({self.openrouter_model})"
            return "offline-template (missing OPENROUTER_API_KEY)"
        if self.openrouter_api_key:
            return f"openrouter ({self.openrouter_model})"
        return "offline-template (set OPENROUTER_API_KEY or provider=ollama)"
