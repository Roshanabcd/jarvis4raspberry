"""FastAPI APIRouter for strictly additive integration of AI Social Media Automation into JARVIS OS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .config import SocialAutomationConfig
from .engine import SocialAutomationEngine
from .llm_provider import SocialLLMClient
from .models import (
    AnalyticsSummaryResponse,
    CreatePostRequest,
    HealthResponse,
    PlanCampaignRequest,
    PlanCampaignResponse,
    PostListResponse,
    PublishPostRequest,
    PublishResult,
    RecordMetricsRequest,
    RunDueResponse,
    SocialPostRecord,
)
from .publisher import SocialPublisher
from .storage import SocialAutomationStore

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(
    config: Optional[SocialAutomationConfig] = None,
    prefix: str = "/api/social-automation",
    ui_route: str = "/social-automation",
) -> APIRouter:
    """Create a self-contained FastAPI router for JARVIS OS."""
    cfg = config or SocialAutomationConfig()
    store = SocialAutomationStore(cfg.db_path)
    llm = SocialLLMClient(cfg)
    publisher = SocialPublisher(cfg)
    engine = SocialAutomationEngine(cfg, store, llm, publisher)

    router = APIRouter(tags=["AI Social Media Automation"])

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
            publish_mode=cfg.publish_mode_label(),
            total_posts=store.count_posts(),
        )

    @router.post(f"{prefix}/plan", response_model=PlanCampaignResponse)
    async def plan_campaign(req: PlanCampaignRequest) -> PlanCampaignResponse:
        return await engine.plan_campaign(req)

    @router.post(f"{prefix}/posts", response_model=SocialPostRecord)
    async def create_post(req: CreatePostRequest) -> SocialPostRecord:
        return engine.create_post(req)

    @router.get(f"{prefix}/posts", response_model=PostListResponse)
    async def list_posts(
        platform: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> PostListResponse:
        rows = store.list_posts(platform=platform, status=status, limit=limit)
        return PostListResponse(
            total=len(rows),
            posts=[SocialPostRecord(**r) for r in rows],
        )

    @router.post(f"{prefix}/posts/{{post_id}}/publish", response_model=PublishResult)
    async def publish_post(post_id: int, req: PublishPostRequest) -> PublishResult:
        try:
            return await engine.publish_post(post_id, dry_run=req.dry_run)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post(f"{prefix}/scheduler/run-due", response_model=RunDueResponse)
    async def run_due(dry_run: bool = Query(default=True)) -> RunDueResponse:
        return await engine.run_due_queue(dry_run=dry_run)

    @router.post(f"{prefix}/posts/{{post_id}}/metrics", response_model=SocialPostRecord)
    async def record_metrics(post_id: int, req: RecordMetricsRequest) -> SocialPostRecord:
        try:
            return engine.record_metrics(post_id, req)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(f"{prefix}/analytics", response_model=AnalyticsSummaryResponse)
    async def analytics() -> AnalyticsSummaryResponse:
        return engine.get_analytics()

    return router
