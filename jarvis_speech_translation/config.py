"""Environment-driven configuration for JARVIS Real-Time Speech Translation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_TRANSLATE_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_speech_translation" / "speech_translation.db").resolve()


@dataclass(frozen=True)
class SpeechTranslationConfig:
    """Immutable runtime settings for bilingual speech translation."""

    db_path: Path = field(default_factory=_default_db_path)
    openrouter_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )
    openrouter_model: str = field(
        default_factory=lambda: os.getenv("JARVIS_TRANSLATE_MODEL", "openrouter/free")
    )
    libretranslate_url: Optional[str] = field(
        default_factory=lambda: os.getenv("JARVIS_TRANSLATE_LIBRE_URL")
    )
