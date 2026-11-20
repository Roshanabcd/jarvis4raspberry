"""Pure-Python 128-D dense semantic embeddings and cosine similarity math."""

from __future__ import annotations

import hashlib
import math
import re
from typing import List

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "into", "about",
}


def compute_dense_embedding(text: str, dim: int = 128) -> List[float]:
    """Build a deterministic L2-normalized dense embedding from word + character trigram projections."""
    vec = [0.0] * dim
    tokens = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 2 and w not in STOPWORDS]

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

    return l2_normalize(vec)


def l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 1e-12:
        return [0.0] * len(vec)
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


def weighted_average_vectors(vectors_and_weights: List[tuple[List[float], float]], dim: int) -> List[float]:
    acc = [0.0] * dim
    total_w = 0.0
    for vec, w in vectors_and_weights:
        if len(vec) != dim:
            continue
        for i in range(dim):
            acc[i] += vec[i] * w
        total_w += abs(w)
    if total_w <= 1e-12:
        return [0.0] * dim
    return l2_normalize(acc)
