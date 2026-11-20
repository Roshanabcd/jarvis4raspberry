"""Hybrid collaborative filtering + SGD neural latent-factor matrix factorization."""

from __future__ import annotations

import hashlib
import math
from typing import Dict, List, Tuple


def _deterministic_vec(key: str, k: int) -> List[float]:
    out: List[float] = []
    for i in range(k):
        h = hashlib.sha256(f"{key}:{i}".encode("utf-8")).digest()
        val = (int.from_bytes(h[:4], "little") / 0xFFFFFFFF) * 0.2 - 0.1
        out.append(val)
    return out


class CollaborativeAndLatentModel:
    """Computes item-item cosine collaborative scores and SGD latent-factor dot products."""

    def __init__(self, latent_dim: int = 16) -> None:
        self.latent_dim = latent_dim

    @staticmethod
    def build_user_item_matrix(interactions: List[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
        matrix: Dict[str, Dict[str, float]] = {}
        for row in interactions:
            u = str(row["user_id"])
            it = str(row["item_id"])
            w = float(row["weight"])
            matrix.setdefault(u, {})
            matrix[u][it] = matrix[u].get(it, 0.0) + w
        return matrix

    @staticmethod
    def item_item_collaborative_scores(
        target_user: str,
        user_item: Dict[str, Dict[str, float]],
        candidate_ids: List[str],
    ) -> Dict[str, float]:
        """Compute item-item collaborative filtering score via cosine similarity over user vectors."""
        user_hist = user_item.get(target_user, {})
        if not user_hist:
            return {cid: 0.0 for cid in candidate_ids}

        # Build item -> {user: weight}
        item_users: Dict[str, Dict[str, float]] = {}
        for u, items in user_item.items():
            for it, w in items.items():
                item_users.setdefault(it, {})[u] = w

        def _item_cos(a: str, b: str) -> float:
            va = item_users.get(a, {})
            vb = item_users.get(b, {})
            if not va or not vb:
                return 0.0
            common = set(va.keys()) & set(vb.keys())
            if not common:
                return 0.0
            dot = sum(va[u] * vb[u] for u in common)
            na = math.sqrt(sum(v * v for v in va.values()))
            nb = math.sqrt(sum(v * v for v in vb.values()))
            return (dot / (na * nb)) if (na > 1e-12 and nb > 1e-12) else 0.0

        scores: Dict[str, float] = {}
        for cid in candidate_ids:
            num = 0.0
            den = 0.0
            for seen_id, w in user_hist.items():
                if seen_id == cid:
                    continue
                sim = _item_cos(cid, seen_id)
                if sim > 0:
                    num += sim * w
                    den += abs(sim)
            scores[cid] = max(0.0, min(1.0, (num / den) / 5.0)) if den > 1e-12 else 0.0
        return scores

    def latent_mf_scores(
        self,
        target_user: str,
        user_item: Dict[str, Dict[str, float]],
        candidate_ids: List[str],
        epochs: int = 18,
        lr: float = 0.05,
        reg: float = 0.02,
    ) -> Dict[str, float]:
        """Train lightweight SGD latent user/item embeddings and score candidates."""
        if target_user not in user_item or len(user_item) < 2:
            return {cid: 0.0 for cid in candidate_ids}

        k = self.latent_dim
        u_vecs: Dict[str, List[float]] = {u: _deterministic_vec(f"u:{u}", k) for u in user_item}
        all_items = set(candidate_ids)
        for items in user_item.values():
            all_items.update(items.keys())
        i_vecs: Dict[str, List[float]] = {it: _deterministic_vec(f"i:{it}", k) for it in all_items}

        samples: List[Tuple[str, str, float]] = []
        for u, items in user_item.items():
            for it, w in items.items():
                samples.append((u, it, max(0.0, min(1.0, w / 5.0))))

        for _ in range(epochs):
            for u, it, target in samples:
                uv = u_vecs[u]
                iv = i_vecs[it]
                pred = sum(uv[d] * iv[d] for d in range(k))
                err = target - pred
                for d in range(k):
                    u_old = uv[d]
                    i_old = iv[d]
                    uv[d] += lr * (err * i_old - reg * u_old)
                    iv[d] += lr * (err * u_old - reg * i_old)

        tu = u_vecs[target_user]
        out: Dict[str, float] = {}
        for cid in candidate_ids:
            iv = i_vecs[cid]
            raw = sum(tu[d] * iv[d] for d in range(k))
            out[cid] = max(0.0, min(1.0, raw))
        return out
