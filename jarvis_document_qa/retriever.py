"""Pure-Python 128-D dense embeddings and hybrid semantic + BM25 lexical retriever."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Dict, List

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "into", "about",
    "what", "when", "where", "which", "does", "have", "been", "were", "will", "how",
    "are", "was", "can", "you", "their", "they", "them", "our", "but", "not",
}


def tokenize(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 2 and w not in STOPWORDS]


def compute_embedding(text: str, dim: int = 128) -> List[float]:
    vec = [0.0] * dim
    tokens = tokenize(text)
    features: List[tuple[str, float]] = []
    for tok in tokens:
        features.append((f"w:{tok}", 1.5))
        if len(tok) >= 4:
            for i in range(len(tok) - 2):
                features.append((f"c:{tok[i:i+3]}", 0.5))

    for feat, weight in features:
        digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
        idx1 = int.from_bytes(digest[:4], "little") % dim
        idx2 = int.from_bytes(digest[4:8], "little") % dim
        sign1 = 1.0 if (digest[0] & 1) == 0 else -1.0
        sign2 = 1.0 if (digest[4] & 1) == 0 else -1.0
        vec[idx1] += sign1 * weight
        vec[idx2] += sign2 * (weight * 0.5)

    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 1e-12:
        return [0.0] * dim
    return [round(x / norm, 6) for x in vec]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def rank_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    dim: int = 128,
    weight_semantic: float = 0.55,
    weight_lexical: float = 0.45,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Rank chunks using hybrid 128-D dense cosine similarity and BM25 lexical scoring."""
    if not chunks:
        return []

    q_vec = compute_embedding(query, dim=dim)
    q_tokens = tokenize(query)
    q_unique = set(q_tokens)

    # Precompute document frequencies for BM25
    n_docs = len(chunks)
    tokenized_chunks = [tokenize(f"{c['section']} {c['content']}") for c in chunks]
    avg_len = (sum(len(t) for t in tokenized_chunks) / n_docs) if n_docs else 1.0
    df: Dict[str, int] = {}
    for toks in tokenized_chunks:
        for tok in set(toks):
            df[tok] = df.get(tok, 0) + 1

    raw_bm25: List[float] = []
    k1 = 1.5
    b = 0.75
    for toks in tokenized_chunks:
        if not q_unique or not toks:
            raw_bm25.append(0.0)
            continue
        tf_map: Dict[str, int] = {}
        for t in toks:
            tf_map[t] = tf_map.get(t, 0) + 1
        dl = len(toks)
        score = 0.0
        for qt in q_unique:
            tf = tf_map.get(qt, 0)
            if tf == 0:
                continue
            idf = math.log(1.0 + (n_docs - df.get(qt, 0) + 0.5) / (df.get(qt, 0) + 0.5))
            score += idf * ((tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (dl / max(avg_len, 1.0)))))
        raw_bm25.append(score)

    max_bm25 = max(raw_bm25, default=0.0)

    scored: List[Dict[str, Any]] = []
    for ch, bm25_val in zip(chunks, raw_bm25):
        sem = max(0.0, cosine_similarity(q_vec, ch["embedding"]))
        lex = (bm25_val / max_bm25) if max_bm25 > 1e-12 else 0.0
        hybrid = weight_semantic * sem + weight_lexical * lex
        scored.append(
            {
                "doc_id": ch["doc_id"],
                "doc_title": ch["doc_title"],
                "filename": ch["filename"],
                "chunk_index": ch["chunk_index"],
                "section": ch["section"],
                "content": ch["content"],
                "score": round(hybrid, 4),
                "semantic_score": round(sem, 4),
                "lexical_score": round(lex, 4),
            }
        )

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]
