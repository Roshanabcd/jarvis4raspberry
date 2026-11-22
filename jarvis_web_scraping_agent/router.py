"""FastAPI APIRouter for strictly additive integration of Autonomous Web Scraping Agent into JARVIS OS."""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from .config import WebScraperConfig
from .engine import WebScraperEngine
from .models import (
    ChangeCheckResponse,
    CheckMonitorRequest,
    CreateMonitorRequest,
    ExtractedPage,
    ExtractRequest,
    HealthResponse,
    MonitorListResponse,
    MonitorRecord,
    SnapshotListResponse,
    SnapshotSummary,
)
from .policy import PolicyViolationError, ScrapePolicyGuard
from .storage import WebScraperStore

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(
    config: Optional[WebScraperConfig] = None,
    prefix: str = "/api/web-scraper",
    ui_route: str = "/web-scraper",
) -> APIRouter:
    """Create a self-contained FastAPI router for JARVIS OS."""
    cfg = config or WebScraperConfig()
    policy = ScrapePolicyGuard(cfg)
    store = WebScraperStore(cfg.db_path)
    engine = WebScraperEngine(cfg, policy, store)

    router = APIRouter(tags=["Autonomous Web Scraping Agent"])

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
            respect_robots_txt=cfg.respect_robots_txt,
            active_monitors=c["active_monitors"],
            total_snapshots=c["total_snapshots"],
        )

    @router.post(f"{prefix}/extract", response_model=ExtractedPage)
    async def extract_page(req: ExtractRequest) -> ExtractedPage:
        try:
            return await engine.extract(req)
        except PolicyViolationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise HTTPException(status_code=502, detail=f"Fetch failed: {exc}") from exc

    @router.post(f"{prefix}/monitors", response_model=MonitorRecord)
    async def create_monitor(req: CreateMonitorRequest) -> MonitorRecord:
        try:
            return engine.create_monitor(req)
        except PolicyViolationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @router.get(f"{prefix}/monitors", response_model=MonitorListResponse)
    async def list_monitors() -> MonitorListResponse:
        rows = store.list_monitors()
        return MonitorListResponse(total=len(rows), monitors=[MonitorRecord(**r) for r in rows])

    @router.post(f"{prefix}/monitors/{{monitor_id}}/check", response_model=ChangeCheckResponse)
    async def check_monitor(
        monitor_id: int,
        req: Optional[CheckMonitorRequest] = None,
    ) -> ChangeCheckResponse:
        override = req.raw_html_override if req else None
        try:
            return await engine.check_monitor(monitor_id, raw_html_override=override)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PolicyViolationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise HTTPException(status_code=502, detail=f"Monitor fetch failed: {exc}") from exc

    @router.get(f"{prefix}/snapshots", response_model=SnapshotListResponse)
    async def list_snapshots(limit: int = Query(default=50, ge=1, le=200)) -> SnapshotListResponse:
        rows = store.list_snapshots(limit=limit)
        return SnapshotListResponse(total=len(rows), snapshots=[SnapshotSummary(**r) for r in rows])

    @router.get(f"{prefix}/snapshots/{{snapshot_id}}/export", response_class=PlainTextResponse)
    async def export_snapshot_json(snapshot_id: int) -> PlainTextResponse:
        snap = store.get_snapshot(snapshot_id)
        if not snap:
            raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found.")
        return PlainTextResponse(
            content=json.dumps(snap, indent=2, ensure_ascii=False),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="jarvis_scrape_snapshot_{snapshot_id}.json"'},
        )

    return router
