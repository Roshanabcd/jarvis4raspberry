"""128-D dense embeddings, BM25 lexical scoring, and Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Dict, List

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "into", "about",
    "what", "when", "where", "which", "does", "have", "been", "were", "will", "how",
}


def tokenize(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9_]+", text.lower()) if len(w) >= 2 and w not in STOPWORDS]


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


def build_snippet(content: str, query_tokens: List[str], max_len: int = 240) -> str:
    clean = " ".join(content.split())
    if len(clean) <= max_len:
        return clean
    lower = clean.lower()
    pos = -1
    for qt in query_tokens:
        idx = lower.find(qt)
        if idx != -1:
            pos = idx
            break
    if pos == -1:
        return clean[:max_len].rstrip() + "..."
    start = max(0, pos - 60)
    end = min(len(clean), start + max_len)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(clean) else ""
    return f"{prefix}{clean[start:end].strip()}{suffix}"


def hybrid_rrf_search(
    query: str,
    chunks: List[Dict[str, Any]],
    dim: int = 128,
    rrf_k: int = 40,
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """Fuse 128-D semantic cosine ranking and BM25 lexical ranking using Reciprocal Rank Fusion."""
    if not chunks:
        return []

    q_vec = compute_embedding(query, dim=dim)
    q_tokens = tokenize(query)
    q_unique = set(q_tokens)
    q_lower = query.strip().lower()

    n_docs = len(chunks)
    tokenized = [tokenize(f"{c['title']} {c['location']} {c['content']}") for c in chunks]
    avg_len = (sum(len(t) for t in tokenized) / n_docs) if n_docs else 1.0
    df: Dict[str, int] = {}
    for toks in tokenized:
        for tok in set(toks):
            df[tok] = df.get(tok, 0) + 1

    sem_scores: List[float] = []
    lex_raw: List[float] = []
    k1 = 1.5
    b = 0.75
    for ch, toks in zip(chunks, tokenized):
        sem = max(0.0, cosine_similarity(q_vec, ch["embedding"]))
        sem_scores.append(sem)

        if not q_unique or not toks:
            lex_raw.append(0.0)
            continue
        tf_map: Dict[str, int] = {}
        for t in toks:
            tf_map[t] = tf_map.get(t, 0) + 1
        dl = len(toks)
        bm25 = 0.0
        for qt in q_unique:
            tf = tf_map.get(qt, 0)
            if tf == 0:
                continue
            idf = math.log(1.0 + (n_docs - df.get(qt, 0) + 0.5) / (df.get(qt, 0) + 0.5))
            bm25 += idf * ((tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (dl / max(avg_len, 1.0)))))
        if q_lower and q_lower in ch["content"].lower():
            bm25 *= 1.25
        lex_raw.append(bm25)

    max_lex = max(lex_raw, default=0.0)
    lex_norm = [(v / max_lex) if max_lex > 1e-12 else 0.0 for v in lex_raw]

    # Compute ranks for RRF
    sem_order = sorted(range(n_docs), key=lambda i: sem_scores[i], reverse=True)
    lex_order = sorted(range(n_docs), key=lambda i: lex_norm[i], reverse=True)
    sem_rank = {idx: rank + 1 for rank, idx in enumerate(sem_order)}
    lex_rank = {idx: rank + 1 for rank, idx in enumerate(lex_order)}

    results: List[Dict[str, Any]] = []
    for i, ch in enumerate(chunks):
        if sem_scores[i] <= 0.02 and lex_norm[i] <= 0.02:
            continue
        rrf = (1.0 / (rrf_k + sem_rank[i])) + (1.0 / (rrf_k + lex_rank[i]))
        # Tie-break & scale with combined raw relevance
        blended = rrf * 20.0 + 0.30 * sem_scores[i] + 0.30 * lex_norm[i]
        results.append(
            {
                "item_id": ch["item_id"],
                "source_type": ch["source_type"],
                "title": ch["title"],
                "source_uri": ch["source_uri"],
                "chunk_index": ch["chunk_index"],
                "location": ch["location"],
                "snippet": build_snippet(ch["content"], q_tokens),
                "content": ch["content"],
                "rrf_score": round(blended, 4),
                "semantic_score": round(sem_scores[i], 4),
                "lexical_score": round(lex_norm[i], 4),
                "tags": ch["tags"],
            }
        )

    results.sort(key=lambda r: r["rrf_score"], reverse=True)
    return results[:top_k]
