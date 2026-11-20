"""Core orchestration service for the JARVIS Deep Learning Recommendation Engine."""

from __future__ import annotations

from typing import Dict, List, Optional

from .config import RecommendationConfig
from .embeddings import compute_dense_embedding, cosine_similarity, weighted_average_vectors
from .models import (
    CatalogItemRecord,
    CatalogItemRequest,
    CatalogListResponse,
    HealthResponse,
    InteractionRecord,
    InteractionRequest,
    RecommendationRequest,
    RecommendationResponse,
    RecommendedItem,
    SimilarItemsResponse,
)
from .recommender import CollaborativeAndLatentModel
from .storage import RecommendationStore

EVENT_WEIGHTS: Dict[str, float] = {
    "view": 1.0,
    "like": 3.5,
    "bookmark": 4.0,
    "complete": 5.0,
    "dismiss": -2.0,
}


class RecommendationEngine:
    """Hybrid content-embedding + collaborative filtering + latent-factor recommendation service."""

    def __init__(self, config: Optional[RecommendationConfig] = None) -> None:
        self.config = config or RecommendationConfig()
        self.store = RecommendationStore(self.config.db_path)
        self.collab_model = CollaborativeAndLatentModel(latent_dim=self.config.latent_factors)

    def health(self) -> HealthResponse:
        counts = self.store.counts()
        return HealthResponse(
            embedding_dim=self.config.embedding_dim,
            total_items=counts["total_items"],
            total_interactions=counts["total_interactions"],
        )

    def upsert_item(self, req: CatalogItemRequest) -> CatalogItemRecord:
        tags = [t.strip() for t in req.tags if t.strip()]
        corpus = f"{req.title} {req.category} {' '.join(tags)} {req.description}"
        embedding = compute_dense_embedding(corpus, dim=self.config.embedding_dim)
        row = self.store.upsert_item(
            item_id=req.item_id.strip(),
            title=req.title.strip(),
            category=req.category.strip() or "general",
            description=req.description.strip(),
            tags=tags,
            embedding=embedding,
        )
        return CatalogItemRecord(
            item_id=row["item_id"],
            created_at=row["created_at"],
            title=row["title"],
            category=row["category"],
            description=row["description"],
            tags=row["tags"],
        )

    def list_items(self) -> CatalogListResponse:
        rows = self.store.list_items()
        items = [
            CatalogItemRecord(
                item_id=r["item_id"],
                created_at=r["created_at"],
                title=r["title"],
                category=r["category"],
                description=r["description"],
                tags=r["tags"],
            )
            for r in rows
        ]
        return CatalogListResponse(total=len(items), items=items)

    def record_interaction(self, req: InteractionRequest) -> InteractionRecord:
        item = self.store.get_item(req.item_id.strip())
        if item is None:
            raise KeyError(f"Catalog item '{req.item_id}' not found.")

        event = req.event_type.strip().lower()
        weight = float(req.rating) if req.rating is not None else EVENT_WEIGHTS.get(event, 1.0)
        row = self.store.record_interaction(
            user_id=req.user_id.strip(),
            item_id=req.item_id.strip(),
            event_type=event,
            weight=weight,
        )
        return InteractionRecord(**row)

    def recommend(self, req: RecommendationRequest) -> RecommendationResponse:
        all_items = self.store.list_items()
        if not all_items:
            return RecommendationResponse(
                user_id=req.user_id,
                strategy="empty_catalog",
                recommendations=[],
            )

        items_by_id = {it["item_id"]: it for it in all_items}
        interactions = self.store.list_all_interactions()
        user_item = self.collab_model.build_user_item_matrix(interactions)
        user_hist = user_item.get(req.user_id, {})

        candidates = []
        cat_filter = req.category_filter.strip().lower() if req.category_filter else None
        for it in all_items:
            if cat_filter and it["category"].lower() != cat_filter:
                continue
            if req.exclude_interacted and it["item_id"] in user_hist:
                continue
            candidates.append(it)

        if not candidates:
            return RecommendationResponse(
                user_id=req.user_id,
                strategy="no_eligible_candidates",
                recommendations=[],
            )

        # Cold-start path when user has no history yet
        if not user_hist:
            pop_weights: Dict[str, float] = {}
            for u_map in user_item.values():
                for iid, w in u_map.items():
                    if w > 0:
                        pop_weights[iid] = pop_weights.get(iid, 0.0) + w
            max_pop = max(pop_weights.values(), default=1.0) or 1.0

            ranked: List[RecommendedItem] = []
            for it in candidates:
                pop_norm = round(pop_weights.get(it["item_id"], 0.0) / max_pop, 4)
                ranked.append(
                    RecommendedItem(
                        item_id=it["item_id"],
                        title=it["title"],
                        category=it["category"],
                        tags=it["tags"],
                        final_score=pop_norm,
                        content_cosine=0.0,
                        collaborative_score=pop_norm,
                        latent_mf_score=0.0,
                        reason="Cold-start popularity & catalog discovery fallback",
                    )
                )
            ranked.sort(key=lambda r: (r.final_score, r.title), reverse=True)
            return RecommendationResponse(
                user_id=req.user_id,
                strategy="cold_start_popularity",
                recommendations=ranked[: req.top_k],
            )

        # Build user semantic preference vector from interacted items
        vecs_and_weights = [
            (items_by_id[iid]["embedding"], w)
            for iid, w in user_hist.items()
            if iid in items_by_id
        ]
        user_vec = weighted_average_vectors(vecs_and_weights, dim=self.config.embedding_dim)

        candidate_ids = [it["item_id"] for it in candidates]
        cf_scores = self.collab_model.item_item_collaborative_scores(
            req.user_id, user_item, candidate_ids
        )
        mf_scores = self.collab_model.latent_mf_scores(
            req.user_id, user_item, candidate_ids
        )

        w_c = self.config.weight_content_embedding
        w_cf = self.config.weight_collaborative
        w_mf = self.config.weight_latent_mf

        ranked = []
        for it in candidates:
            cid = it["item_id"]
            c_cos = max(0.0, cosine_similarity(user_vec, it["embedding"]))
            cf = cf_scores.get(cid, 0.0)
            mf = mf_scores.get(cid, 0.0)
            final = w_c * c_cos + w_cf * cf + w_mf * mf

            parts = []
            if c_cos >= 0.25:
                parts.append(f"strong 128-D semantic match ({c_cos:.2f})")
            if cf >= 0.20:
                parts.append(f"peer collaborative overlap ({cf:.2f})")
            if mf >= 0.20:
                parts.append(f"latent-factor affinity ({mf:.2f})")
            reason = " + ".join(parts) if parts else "Balanced hybrid embedding and collaborative score"

            ranked.append(
                RecommendedItem(
                    item_id=cid,
                    title=it["title"],
                    category=it["category"],
                    tags=it["tags"],
                    final_score=round(final, 4),
                    content_cosine=round(c_cos, 4),
                    collaborative_score=round(cf, 4),
                    latent_mf_score=round(mf, 4),
                    reason=reason,
                )
            )

        ranked.sort(key=lambda r: r.final_score, reverse=True)
        return RecommendationResponse(
            user_id=req.user_id,
            strategy="hybrid_neural_collaborative",
            recommendations=ranked[: req.top_k],
        )

    def find_similar_items(self, item_id: str, top_k: int = 5) -> SimilarItemsResponse:
        source = self.store.get_item(item_id.strip())
        if source is None:
            raise KeyError(f"Catalog item '{item_id}' not found.")

        all_items = self.store.list_items()
        similar: List[RecommendedItem] = []
        for it in all_items:
            if it["item_id"] == source["item_id"]:
                continue
            cos = max(0.0, cosine_similarity(source["embedding"], it["embedding"]))
            similar.append(
                RecommendedItem(
                    item_id=it["item_id"],
                    title=it["title"],
                    category=it["category"],
                    tags=it["tags"],
                    final_score=round(cos, 4),
                    content_cosine=round(cos, 4),
                    collaborative_score=0.0,
                    latent_mf_score=0.0,
                    reason=f"128-D embedding cosine similarity ({cos:.2f}) to {source['title']}",
                )
            )

        similar.sort(key=lambda r: r.final_score, reverse=True)
        return SimilarItemsResponse(
            source_item_id=source["item_id"],
            similar=similar[: max(1, min(top_k, 50))],
        )
