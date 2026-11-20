"""Environment-driven configuration for JARVIS Customer Support Bot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_SUPPORT_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_support_bot" / "support_bot.db").resolve()


@dataclass(frozen=True)
class SupportBotConfig:
    """Immutable runtime settings supporting OpenAI, OpenRouter, Ollama, and offline KB fallback."""

    db_path: Path = field(default_factory=_default_db_path)

    provider: str = field(
        default_factory=lambda: os.getenv("JARVIS_SUPPORT_PROVIDER", "auto").strip().lower()
    )
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip()
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    )
    openrouter_api_key: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "").strip()
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
        default_factory=lambda: float(os.getenv("JARVIS_SUPPORT_TIMEOUT_SEC", "35"))
    )

    def active_provider_label(self) -> str:
        if self.provider == "offline":
            return "offline-kb"
        if self.provider == "openai" and self.openai_api_key:
            return f"openai ({self.openai_model})"
        if self.provider == "openrouter" and self.openrouter_api_key:
            return f"openrouter ({self.openrouter_model})"
        if self.provider == "ollama":
            return f"ollama ({self.ollama_model})"
        if self.openai_api_key:
            return f"openai ({self.openai_model})"
        if self.openrouter_api_key:
            return f"openrouter ({self.openrouter_model})"
        return "offline-kb (set OPENAI_API_KEY, OPENROUTER_API_KEY, or provider=ollama)"
