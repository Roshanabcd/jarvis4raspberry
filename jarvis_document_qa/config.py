"""Environment-driven configuration for JARVIS Document Question Answering."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_DOCQA_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_document_qa" / "docqa.db").resolve()


@dataclass(frozen=True)
class DocumentQAConfig:
    """Immutable runtime settings for Document Question Answering."""

    db_path: Path = field(default_factory=_default_db_path)
    embedding_dim: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_DOCQA_EMBED_DIM", "128"))
    )
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_DOCQA_CHUNK_SIZE", "520"))
    )
    chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_DOCQA_CHUNK_OVERLAP", "90"))
    )
    weight_semantic: float = 0.55
    weight_lexical: float = 0.45
    openrouter_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )
    openrouter_model: str = field(
        default_factory=lambda: os.getenv("JARVIS_DOCQA_MODEL", "openrouter/free")
    )
