"""Environment-driven configuration for JARVIS Deep Learning Recommendation Engine."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_REC_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_recommendation_engine" / "recommendations.db").resolve()


@dataclass(frozen=True)
class RecommendationConfig:
    """Immutable runtime settings for the hybrid recommendation engine."""

    db_path: Path = field(default_factory=_default_db_path)
    embedding_dim: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_REC_EMBED_DIM", "128"))
    )
    latent_factors: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_REC_LATENT_DIM", "16"))
    )
    # Hybrid blend weights
    weight_content_embedding: float = 0.45
    weight_collaborative: float = 0.35
    weight_latent_mf: float = 0.20
