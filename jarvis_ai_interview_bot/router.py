"""FastAPI APIRouter for strictly additive integration of AI Interview Bot into JARVIS OS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from .config import InterviewBotConfig
from .engine import InterviewBotEngine
from .llm_provider import InterviewLLMClient
from .models import (
    HealthResponse,
    InterviewReportResponse,
    SessionListResponse,
    SessionSummary,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from .storage import InterviewBotStore

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(
    config: Optional[InterviewBotConfig] = None,
    prefix: str = "/api/interview-bot",
    ui_route: str = "/interview-bot",
) -> APIRouter:
    """Create a self-contained FastAPI router for JARVIS OS."""
    cfg = config or InterviewBotConfig()
    store = InterviewBotStore(cfg.db_path)
    llm = InterviewLLMClient(cfg)
    engine = InterviewBotEngine(cfg, store, llm)

    router = APIRouter(tags=["AI Interview Bot"])

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
            total_sessions=store.count_sessions(),
        )

    @router.post(f"{prefix}/sessions/start", response_model=StartInterviewResponse)
    async def start_session(req: StartInterviewRequest) -> StartInterviewResponse:
        return await engine.start_session(req)

    @router.post(f"{prefix}/sessions/{{session_id}}/answer", response_model=SubmitAnswerResponse)
    async def submit_answer(session_id: int, req: SubmitAnswerRequest) -> SubmitAnswerResponse:
        try:
            return await engine.submit_answer(session_id, req)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get(f"{prefix}/sessions/{{session_id}}/report", response_model=InterviewReportResponse)
    async def get_report(session_id: int) -> InterviewReportResponse:
        try:
            return engine.build_report(session_id, finalize=False)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(f"{prefix}/sessions/{{session_id}}/export", response_class=PlainTextResponse)
    async def export_report(session_id: int) -> PlainTextResponse:
        try:
            report = engine.build_report(session_id, finalize=False)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        filename = f"jarvis_interview_report_{session_id}.md"
        return PlainTextResponse(
            content=report.report_markdown,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @router.get(f"{prefix}/sessions", response_model=SessionListResponse)
    async def list_sessions(limit: int = Query(default=30, ge=1, le=200)) -> SessionListResponse:
        rows = store.list_sessions(limit=limit)
        return SessionListResponse(
            total=len(rows),
            sessions=[SessionSummary(**r) for r in rows],
        )

    return router
