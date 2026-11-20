"""FastAPI APIRouter for strictly additive integration of AI Content Creation Pipeline into JARVIS OS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from .config import ContentPipelineConfig
from .llm_provider import ContentLLMClient
from .models import (
    BlogRequest,
    BlogResponse,
    CampaignRequest,
    CampaignResponse,
    CarouselRequest,
    CarouselResponse,
    HealthResponse,
    HooksCaptionsRequest,
    HooksCaptionsResponse,
    LibraryItemDetail,
    LibraryItemSummary,
    LibraryListResponse,
    VideoScriptRequest,
    VideoScriptResponse,
)
from .pipeline import ContentPipelineEngine
from .storage import ContentPipelineStore

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(
    config: Optional[ContentPipelineConfig] = None,
    prefix: str = "/api/content-pipeline",
    ui_route: str = "/content-pipeline",
) -> APIRouter:
    """Create a self-contained FastAPI router for JARVIS OS."""
    cfg = config or ContentPipelineConfig()
    store = ContentPipelineStore(cfg.db_path)
    llm = ContentLLMClient(cfg)
    engine = ContentPipelineEngine(cfg, store, llm)

    router = APIRouter(tags=["AI Content Creation Pipeline"])

    @router.get(ui_route, response_class=HTMLResponse, include_in_schema=False)
    async def serve_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=404, detail="UI bundle not found.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get(f"{prefix}/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            provider=cfg.active_provider_label(),
            saved_items=store.count_items(),
        )

    @router.post(f"{prefix}/blog", response_model=BlogResponse)
    async def generate_blog(req: BlogRequest) -> BlogResponse:
        return await engine.generate_blog(req)

    @router.post(f"{prefix}/video-script", response_model=VideoScriptResponse)
    async def generate_video_script(req: VideoScriptRequest) -> VideoScriptResponse:
        return await engine.generate_video_script(req)

    @router.post(f"{prefix}/hooks-captions", response_model=HooksCaptionsResponse)
    async def generate_hooks_captions(req: HooksCaptionsRequest) -> HooksCaptionsResponse:
        return await engine.generate_hooks_captions(req)

    @router.post(f"{prefix}/carousel", response_model=CarouselResponse)
    async def generate_carousel(req: CarouselRequest) -> CarouselResponse:
        return await engine.generate_carousel(req)

    @router.post(f"{prefix}/campaign", response_model=CampaignResponse)
    async def generate_campaign(req: CampaignRequest) -> CampaignResponse:
        return await engine.generate_campaign(req)

    @router.get(f"{prefix}/history", response_model=LibraryListResponse)
    async def list_history(
        content_type: Optional[str] = Query(default=None),
        limit: int = Query(default=30, ge=1, le=200),
    ) -> LibraryListResponse:
        rows = store.list_items(content_type=content_type, limit=limit)
        return LibraryListResponse(
            total=len(rows),
            items=[LibraryItemSummary(**r) for r in rows],
        )

    @router.get(f"{prefix}/item/{{item_id}}", response_model=LibraryItemDetail)
    async def get_item(item_id: int) -> LibraryItemDetail:
        item = store.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Content item {item_id} not found.")
        return LibraryItemDetail(**item)

    @router.get(f"{prefix}/item/{{item_id}}/export", response_class=PlainTextResponse)
    async def export_item_markdown(item_id: int) -> PlainTextResponse:
        item = store.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Content item {item_id} not found.")
        filename = f"jarvis_{item['content_type']}_{item_id}.md"
        return PlainTextResponse(
            content=str(item["markdown"]),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return router
