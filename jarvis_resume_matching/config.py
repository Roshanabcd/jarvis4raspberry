"""Environment-driven configuration for JARVIS Smart Resume Matching."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_RESUME_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_resume_matching" / "resume_matching.db").resolve()


@dataclass(frozen=True)
class ResumeMatchingConfig:
    """Immutable runtime settings for Smart Resume Matching."""

    db_path: Path = field(default_factory=_default_db_path)
    embedding_dim: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_RESUME_EMBED_DIM", "128"))
    )
    weight_required_skills: float = 0.45
    weight_preferred_skills: float = 0.15
    weight_semantic: float = 0.25
    weight_experience: float = 0.15
