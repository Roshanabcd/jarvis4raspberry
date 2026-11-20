"""Environment-driven configuration for JARVIS End-to-End AI Search Engine."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_SEARCH_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_ai_search_engine" / "search_index.db").resolve()


def _default_allowed_roots() -> List[Path]:
    raw = os.getenv("JARVIS_SEARCH_ALLOWED_ROOTS", "")
    if raw.strip():
        return [Path(p.strip()).expanduser().resolve() for p in raw.split(":") if p.strip()]
    return [Path.cwd().resolve()]


@dataclass(frozen=True)
class AISearchConfig:
    """Immutable runtime settings for the unified AI Search Engine."""

    db_path: Path = field(default_factory=_default_db_path)
    allowed_roots: List[Path] = field(default_factory=_default_allowed_roots)
    embedding_dim: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_SEARCH_EMBED_DIM", "128"))
    )
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_SEARCH_CHUNK_SIZE", "540"))
    )
    chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_SEARCH_CHUNK_OVERLAP", "80"))
    )
    max_file_bytes: int = 512_000
    rrf_k: int = 40
    openrouter_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )
    openrouter_model: str = field(
        default_factory=lambda: os.getenv("JARVIS_SEARCH_MODEL", "openrouter/free")
    )
