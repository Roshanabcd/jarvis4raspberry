"""FastAPI APIRouter and WebSocket live stream endpoint for JARVIS Real-Time Object Detection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .config import ObjectDetectionConfig
from .engine import ObjectDetectionEngine
from .models import (
    AlertListResponse,
    AnalyticsResponse,
    CreateZoneRequest,
    DetectFrameRequest,
    DetectFrameResponse,
    HealthResponse,
    ZoneListResponse,
    ZoneRecord,
)

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[ObjectDetectionConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = ObjectDetectionEngine(config=config)
    router = APIRouter(tags=["JARVIS Real-Time Object Detection"])

    @router.get("/object-detection", response_class=HTMLResponse, include_in_schema=False)
    def object_detection_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Object Detection UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/object-detection/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/object-detection/detect", response_model=DetectFrameResponse)
    def detect_frame(req: DetectFrameRequest) -> DetectFrameResponse:
        try:
            return engine.detect_frame(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/object-detection/zones", response_model=ZoneRecord)
    def upsert_zone(req: CreateZoneRequest) -> ZoneRecord:
        try:
            return engine.upsert_zone(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/object-detection/zones", response_model=ZoneListResponse)
    def list_zones() -> ZoneListResponse:
        return engine.list_zones()

    @router.delete("/api/object-detection/zones/{zone_id}")
    def delete_zone(zone_id: int) -> dict:
        if not engine.delete_zone(zone_id):
            raise HTTPException(status_code=404, detail=f"Zone #{zone_id} not found.")
        return {"deleted": True, "zone_id": zone_id}

    @router.get("/api/object-detection/alerts", response_model=AlertListResponse)
    def list_alerts(limit: int = Query(default=50, ge=1, le=200)) -> AlertListResponse:
        return engine.list_alerts(limit=limit)

    @router.get("/api/object-detection/analytics", response_model=AnalyticsResponse)
    def analytics() -> AnalyticsResponse:
        return engine.analytics()

    @router.websocket("/api/object-detection/ws/stream")
    async def ws_detect_stream(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json({"event": "connected", "backend": engine.detector.active_backend_name()})
        try:
            while True:
                payload = await websocket.receive_json()
                img_b64 = str(payload.get("image_base64", "")).strip()
                if not img_b64:
                    continue
                try:
                    res = engine.detect_frame(
                        DetectFrameRequest(
                            image_base64=img_b64,
                            confidence_threshold=payload.get("confidence_threshold"),
                            target_classes=payload.get("target_classes") or [],
                            stream_id=str(payload.get("stream_id", "live_cam")),
                        )
                    )
                    await websocket.send_json(res.dict())
                except Exception as exc:
                    await websocket.send_json({"error": str(exc)})
        except WebSocketDisconnect:
            return

    return router
