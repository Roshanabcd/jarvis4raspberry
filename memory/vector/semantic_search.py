"""
JARVIS OS — Configurable Semantic Retrieval for Long-Term Memory.

Wraps the existing ``MemoryDB`` keyword search with an optional lightweight
semantic reranking pass (TF-IDF / cosine similarity over numpy).  No external
ML models are required: when a real embedding provider is unavailable the
module degrades gracefully to plain keyword search and reports
``semantic: False`` so callers never mistake a keyword match for vector search.

All behaviour is controlled through ``config.yaml`` under the ``memory`` key:

    memory:
      semantic_search:
        enabled: true
        similarity_threshold: 0.25
        max_candidates: 50
"""
from __future__ import annotations

import json
import logging
import math
import re
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("JARVIS.Memory.Semantic")

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return [t for t in _WORD_RE.findall(text.lower()) if len(t) > 2]


class SemanticMemorySearch:
    """Configurable semantic retrieval over ``MemoryDB``.

    The first call to :meth:`search` builds an in-memory TF-IDF index from the
    candidate memories returned by ``MemoryDB.search``.  Results are reranked by
    cosine similarity between the query vector and each memory vector when
    semantic search is enabled; otherwise keyword order is preserved.
    """

    def __init__(self, db, enabled: bool = True,
                 similarity_threshold: float = 0.25,
                 max_candidates: int = 50) -> None:
        self.db = db
        self.enabled = bool(enabled)
        self.similarity_threshold = float(similarity_threshold)
        self.max_candidates = int(max_candidates)
        self._index_built = False
        self._doc_tokens: List[List[str]] = []
        self._idf: Dict[str, float] = {}

    # ------------------------------------------------------------------ #
    # Indexing
    # ------------------------------------------------------------------ #
    def _build_index(self, docs: List[Dict[str, Any]]) -> None:
        """Build a TF-IDF index over the supplied candidate documents."""
        self._doc_tokens = [_tokenize(d.get("content", "") or "") for d in docs]
        doc_count = max(1, len(self._doc_tokens))

        # Document frequency per term
        df: Dict[str, int] = {}
        for tokens in self._doc_tokens:
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1

        self._idf = {
            term: math.log(doc_count / (1 + freq)) for term, freq in df.items()
        }
        self._index_built = True

    def _vectorize(self, tokens: List[str]) -> np.ndarray:
        if not self._idf:
            return np.zeros(0, dtype=float)
        vec = {}
        for term in tokens:
            if term in self._idf:
                vec[term] = vec.get(term, 0) + 1
        # TF-IDF weighting
        terms = list(self._idf.keys())
        if not terms:
            return np.zeros(0, dtype=float)
        arr = np.zeros(len(terms), dtype=float)
        for i, term in enumerate(terms):
            arr[i] = vec.get(term, 0) * self._idf[term]
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        if a.size == 0 or b.size == 0:
            return 0.0
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def search(self, query: str = "", category: Optional[str] = None,
               limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve memories, optionally reranked by semantic similarity.

        Returns each memory dict augmented with ``semantic`` (bool) and, when
        semantic reranking is enabled, ``similarity`` (float).

        When semantic mode is enabled the query is used for ranking rather than
        as a hard substring filter, so conceptual queries (e.g. "capital city")
        can surface relevant memories even when the exact phrase is absent.
        """
        # Pull a candidate pool larger than the final limit so reranking can
        # surface the best semantic matches.  In semantic mode we do not apply
        # the content substring filter here; the similarity score does that.
        if self.enabled and query:
            pool = self.db.search(query="", category=category,
                                  limit=max(self.max_candidates, limit))
        else:
            pool = self.db.search(query=query, category=category,
                                  limit=max(self.max_candidates, limit))
        if not pool or not self.enabled:
            for d in pool:
                d.setdefault("semantic", False)
            return pool[:limit]

        self._build_index(pool)
        query_vec = self._vectorize(_tokenize(query))

        scored: List[tuple[float, Dict[str, Any]]] = []
        for idx, doc in enumerate(pool):
            doc_vec = self._vectorize(self._doc_tokens[idx])
            sim = self._cosine(query_vec, doc_vec)
            enriched = dict(doc)
            enriched["semantic"] = True
            enriched["similarity"] = round(sim, 4)
            if sim >= self.similarity_threshold:
                scored.append((sim, enriched))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [doc for _, doc in scored[:limit]]
        logger.debug(
            "Semantic search query=%r category=%s candidates=%d returned=%d",
            query, category, len(pool), len(results),
        )
        return results

    def status(self) -> Dict[str, Any]:
        """Return configuration and capability status (never exposes data)."""
        return {
            "enabled": self.enabled,
            "similarity_threshold": self.similarity_threshold,
            "max_candidates": self.max_candidates,
            "index_built": self._index_built,
        }


# Module-level singleton bound to the default MemoryDB.
from memory.long_term.database import db as _default_db  # noqa: E402
from config.config_manager import config  # noqa: E402

_mem_cfg = config.get("memory", {}) or {}
_sem_cfg = _mem_cfg.get("semantic_search", {}) or {}

semantic_search = SemanticMemorySearch(
    db=_default_db,
    enabled=bool(_sem_cfg.get("enabled", True)),
    similarity_threshold=float(_sem_cfg.get("similarity_threshold", 0.25)),
    max_candidates=int(_sem_cfg.get("max_candidates", 50)),
)
