"""Environment-driven configuration for JARVIS AI Social Media Automation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_SOCIAL_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_social_automation" / "social_automation.db").resolve()


def _default_export_dir() -> Path:
    env_dir = os.getenv("JARVIS_SOCIAL_EXPORT_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return (Path.cwd() / ".jarvis_social_automation" / "manual_exports").resolve()


@dataclass(frozen=True)
class SocialAutomationConfig:
    """Immutable runtime settings for AI Social Media Automation."""

    db_path: Path = field(default_factory=_default_db_path)
    manual_export_dir: Path = field(default_factory=_default_export_dir)

    provider: str = field(
        default_factory=lambda: os.getenv("JARVIS_SOCIAL_PROVIDER", "auto").strip().lower()
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

    # Optional webhook URL (e.g., n8n / Make / Zapier / custom publisher bridge)
    publish_webhook_url: str = field(
        default_factory=lambda: os.getenv("JARVIS_SOCIAL_WEBHOOK_URL", "").strip()
    )
    publish_webhook_token: str = field(
        default_factory=lambda: os.getenv("JARVIS_SOCIAL_WEBHOOK_TOKEN", "").strip()
    )
    request_timeout_sec: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_SOCIAL_TIMEOUT_SEC", "30"))
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

    def publish_mode_label(self) -> str:
        if self.publish_webhook_url:
            return "webhook-bridge"
        return "manual-export-fallback"
