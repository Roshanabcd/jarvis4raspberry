"""FastAPI APIRouter for JARVIS Deep Learning Recommendation Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .config import RecommendationConfig
from .engine import RecommendationEngine
from .models import (
    CatalogItemRecord,
    CatalogItemRequest,
    CatalogListResponse,
    HealthResponse,
    InteractionRecord,
    InteractionRequest,
    RecommendationRequest,
    RecommendationResponse,
    SimilarItemsResponse,
)

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[RecommendationConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = RecommendationEngine(config=config)
    router = APIRouter(tags=["JARVIS Recommendation Engine"])

    @router.get("/recommendations", response_class=HTMLResponse, include_in_schema=False)
    def recommendations_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Recommendation UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/recommendations/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/recommendations/items", response_model=CatalogItemRecord)
    def upsert_item(req: CatalogItemRequest) -> CatalogItemRecord:
        return engine.upsert_item(req)

    @router.get("/api/recommendations/items", response_model=CatalogListResponse)
    def list_items() -> CatalogListResponse:
        return engine.list_items()

    @router.post("/api/recommendations/interactions", response_model=InteractionRecord)
    def log_interaction(req: InteractionRequest) -> InteractionRecord:
        try:
            return engine.record_interaction(req)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/api/recommendations/recommend", response_model=RecommendationResponse)
    def get_recommendations(req: RecommendationRequest) -> RecommendationResponse:
        return engine.recommend(req)

    @router.get(
        "/api/recommendations/items/{item_id}/similar",
        response_model=SimilarItemsResponse,
    )
    def get_similar_items(
        item_id: str,
        top_k: int = Query(default=5, ge=1, le=50),
    ) -> SimilarItemsResponse:
        try:
            return engine.find_similar_items(item_id=item_id, top_k=top_k)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
