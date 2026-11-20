"""Environment-driven configuration for JARVIS Personalized Learning AI Coach."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_COACH_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_learning_coach" / "learning_coach.db").resolve()


@dataclass(frozen=True)
class LearningCoachConfig:
    """Immutable runtime settings for the Personalized Learning AI Coach."""

    db_path: Path = field(default_factory=_default_db_path)
    openrouter_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )
    openrouter_model: str = field(
        default_factory=lambda: os.getenv("JARVIS_COACH_MODEL", "openrouter/free")
    )
