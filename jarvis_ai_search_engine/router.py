"""FastAPI APIRouter for JARVIS End-to-End AI Search Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .config import AISearchConfig
from .engine import AISearchEngine
from .models import (
    DeleteSourceResponse,
    HealthResponse,
    IndexDirectoryRequest,
    IndexDirectoryResponse,
    IndexSourceRequest,
    SearchHistoryResponse,
    SearchQueryRequest,
    SearchQueryResponse,
    SourceListResponse,
    SourceRecord,
)

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[AISearchConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = AISearchEngine(config=config)
    router = APIRouter(tags=["JARVIS AI Search Engine"])

    @router.get("/ai-search", response_class=HTMLResponse, include_in_schema=False)
    def ai_search_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="AI Search UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/ai-search/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/ai-search/index", response_model=SourceRecord)
    def index_source(req: IndexSourceRequest) -> SourceRecord:
        try:
            return engine.index_source(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/ai-search/index-directory", response_model=IndexDirectoryResponse)
    def index_directory(req: IndexDirectoryRequest) -> IndexDirectoryResponse:
        try:
            return engine.index_directory(req)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/ai-search/sources", response_model=SourceListResponse)
    def list_sources() -> SourceListResponse:
        return engine.list_sources()

    @router.delete("/api/ai-search/sources/{item_id}", response_model=DeleteSourceResponse)
    def delete_source(item_id: str) -> DeleteSourceResponse:
        try:
            return engine.delete_source(item_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/api/ai-search/query", response_model=SearchQueryResponse)
    def search_query(req: SearchQueryRequest) -> SearchQueryResponse:
        return engine.query(req)

    @router.get("/api/ai-search/history", response_model=SearchHistoryResponse)
    def search_history(limit: int = Query(default=25, ge=1, le=100)) -> SearchHistoryResponse:
        return engine.history(limit=limit)

    return router
