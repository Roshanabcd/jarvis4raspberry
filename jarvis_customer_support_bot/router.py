"""FastAPI APIRouter for strictly additive integration of Customer Support Bot into JARVIS OS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .config import SupportBotConfig
from .engine import SupportBotEngine
from .llm_provider import SupportLLMClient
from .models import (
    CustomerInquiryRequest,
    HealthResponse,
    KBArticleRecord,
    KBArticleRequest,
    KBListResponse,
    SupportReplyResponse,
    SupportStatsResponse,
    TicketListResponse,
    TicketRecord,
    UpdateTicketRequest,
)
from .storage import SupportBotStore

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(
    config: Optional[SupportBotConfig] = None,
    prefix: str = "/api/support-bot",
    ui_route: str = "/support-bot",
) -> APIRouter:
    """Create a self-contained FastAPI router for JARVIS OS."""
    cfg = config or SupportBotConfig()
    store = SupportBotStore(cfg.db_path)
    llm = SupportLLMClient(cfg)
    engine = SupportBotEngine(cfg, store, llm)

    router = APIRouter(tags=["ChatGPT-Powered Customer Support Bot"])

    @router.get(ui_route, response_class=HTMLResponse, include_in_schema=False)
    async def serve_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=404, detail="UI bundle not found.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get(f"{prefix}/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        c = store.counts()
        return HealthResponse(
            status="ok",
            provider=cfg.active_provider_label(),
            kb_articles=c["kb_articles"],
            open_tickets=c["open_tickets"],
        )

    @router.post(f"{prefix}/kb", response_model=KBArticleRecord)
    async def add_kb(req: KBArticleRequest) -> KBArticleRecord:
        row = store.add_kb_article(req.title, req.category, req.content, req.tags)
        return KBArticleRecord(**row)

    @router.get(f"{prefix}/kb", response_model=KBListResponse)
    async def list_kb() -> KBListResponse:
        rows = store.list_kb_articles()
        return KBListResponse(total=len(rows), articles=[KBArticleRecord(**r) for r in rows])

    @router.post(f"{prefix}/inquire", response_model=SupportReplyResponse)
    async def handle_inquiry(req: CustomerInquiryRequest) -> SupportReplyResponse:
        return await engine.handle_inquiry(req)

    @router.get(f"{prefix}/tickets", response_model=TicketListResponse)
    async def list_tickets(
        status: Optional[str] = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> TicketListResponse:
        rows = store.list_tickets(status=status, limit=limit)
        return TicketListResponse(total=len(rows), tickets=[TicketRecord(**r) for r in rows])

    @router.patch(f"{prefix}/tickets/{{ticket_id}}", response_model=TicketRecord)
    async def update_ticket(ticket_id: int, req: UpdateTicketRequest) -> TicketRecord:
        if req.status.lower() not in ("open", "escalated", "resolved"):
            raise HTTPException(status_code=400, detail="status must be open, escalated, or resolved.")
        row = store.update_ticket_status(ticket_id, req.status)
        if not row:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")
        return TicketRecord(**row)

    @router.get(f"{prefix}/stats", response_model=SupportStatsResponse)
    async def stats() -> SupportStatsResponse:
        return engine.get_stats()

    return router
