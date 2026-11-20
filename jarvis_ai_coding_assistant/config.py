"""Environment-driven configuration for JARVIS AI Coding Assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple


def _default_workspace() -> Path:
    env_ws = os.getenv("JARVIS_CODE_WORKSPACE")
    if env_ws:
        return Path(env_ws).expanduser().resolve()
    candidate = Path("~/.gemini/antigravity/scratch/jarvis-os").expanduser()
    if candidate.exists():
        return candidate.resolve()
    return Path.cwd().resolve()


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_CODING_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_coding_assistant" / "coding_assistant.db").resolve()


@dataclass(frozen=True)
class CodingAssistantConfig:
    """Immutable runtime settings for the AI Coding Assistant module."""

    workspace_root: Path = field(default_factory=_default_workspace)
    db_path: Path = field(default_factory=_default_db_path)

    # Provider settings (matches JARVIS OS OpenRouter + Local Ollama setup)
    provider: str = field(
        default_factory=lambda: os.getenv("JARVIS_CODING_PROVIDER", "auto").strip().lower()
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
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b").strip()
    )

    request_timeout_sec: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_CODING_TIMEOUT_SEC", "45"))
    )
    max_file_bytes: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_CODING_MAX_FILE_BYTES", str(256 * 1024)))
    )
    max_list_files: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_CODING_MAX_LIST_FILES", "400"))
    )
    ignored_dirs: Tuple[str, ...] = (
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
        ".jarvis_coding_assistant",
    )
    allow_workspace_writes: bool = field(
        default_factory=lambda: os.getenv("JARVIS_CODING_ALLOW_WRITES", "true").lower()
        in ("1", "true", "yes")
    )

    def active_provider_label(self) -> str:
        """Describe which provider will be tried first."""
        if self.provider == "offline":
            return "offline-local"
        if self.provider == "ollama":
            return f"ollama ({self.ollama_model})"
        if self.provider == "openrouter":
            if self.openrouter_api_key:
                return f"openrouter ({self.openrouter_model})"
            return "offline-local (missing OPENROUTER_API_KEY)"
        # auto mode
        if self.openrouter_api_key:
            return f"openrouter ({self.openrouter_model})"
        return "offline-local (set OPENROUTER_API_KEY or provider=ollama)"
