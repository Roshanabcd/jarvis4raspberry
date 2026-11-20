"""FastAPI APIRouter for JARVIS Fraud Detection System."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .config import FraudDetectionConfig
from .engine import FraudDetectionEngine
from .models import (
    AlertListResponse,
    AlertRecord,
    AlertUpdateRequest,
    AnalyticsSummaryResponse,
    BatchEventsRequest,
    BatchEventsResponse,
    EventListResponse,
    HealthResponse,
    ScoredEventRecord,
    SecurityEventRequest,
)

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[FraudDetectionConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = FraudDetectionEngine(config=config)
    router = APIRouter(tags=["JARVIS Fraud Detection"])

    @router.get("/fraud-detection", response_class=HTMLResponse, include_in_schema=False)
    def fraud_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Fraud Detection UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/fraud-detection/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/fraud-detection/events", response_model=ScoredEventRecord)
    def ingest_event(req: SecurityEventRequest) -> ScoredEventRecord:
        try:
            return engine.ingest_event(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/fraud-detection/events/batch", response_model=BatchEventsResponse)
    def ingest_batch(req: BatchEventsRequest) -> BatchEventsResponse:
        try:
            return engine.ingest_batch(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/fraud-detection/events", response_model=EventListResponse)
    def list_events(
        limit: int = Query(default=50, ge=1, le=200),
        stream_type: Optional[str] = None,
    ) -> EventListResponse:
        return engine.list_events(limit=limit, stream_type=stream_type)

    @router.get("/api/fraud-detection/alerts", response_model=AlertListResponse)
    def list_alerts(
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = Query(default=50, ge=1, le=200),
    ) -> AlertListResponse:
        return engine.list_alerts(status=status, severity=severity, limit=limit)

    @router.patch("/api/fraud-detection/alerts/{alert_id}", response_model=AlertRecord)
    def update_alert(alert_id: int, req: AlertUpdateRequest) -> AlertRecord:
        try:
            return engine.update_alert(alert_id=alert_id, req=req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/api/fraud-detection/summary", response_model=AnalyticsSummaryResponse)
    def summary() -> AnalyticsSummaryResponse:
        return engine.summary()

    return router
