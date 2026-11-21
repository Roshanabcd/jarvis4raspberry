"""FastAPI REST & WebSocket routes for JARVIS Module 36 — Screen Vision Assistant."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_36_screen_vision_assistant.backend.models.database import utc_now_iso
from modules.module_36_screen_vision_assistant.backend.models.schemas import CaptureCreateRequest, HitTestRequest, ScreenQueryRequest, model_to_dict
from modules.module_36_screen_vision_assistant.backend.services.vision_engine import VisionEngine, VisionError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: VisionError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: VisionEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/vision", tags=["JARVIS Module 36 — Screen Vision Assistant"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-36-screen-vision-assistant",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.is_simulated,
            "timestamp": utc_now_iso(),
        }

    @router.get("/manifest")
    async def manifest() -> Dict[str, Any]:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="manifest.json not found")

    @router.get("/status")
    async def status() -> Dict[str, Any]:
        return engine.get_status()

    @router.get("/captures")
    async def list_captures() -> Dict[str, Any]:
        caps = engine.db.list_captures()
        return {"captures": caps, "count": len(caps)}

    @router.post("/captures", status_code=201)
    async def create_capture(body: CaptureCreateRequest) -> Any:
        try:
            return engine.create_capture(model_to_dict(body))
        except VisionError as exc:
            return _err(exc)

    @router.post("/captures/{capture_id}/hit-test")
    async def hit_test(capture_id: str, body: HitTestRequest) -> Any:
        try:
            return engine.hit_test(capture_id, body.x, body.y)
        except VisionError as exc:
            return _err(exc)

    @router.post("/captures/{capture_id}/query", status_code=201)
    async def query_capture(capture_id: str, body: ScreenQueryRequest) -> Any:
        try:
            return engine.query_capture(capture_id, body.question)
        except VisionError as exc:
            return _err(exc)

    @router.get("/queries")
    async def list_queries(capture_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        items = engine.db.list_queries(capture_id=capture_id)
        return {"queries": items, "count": len(items)}

    @router.websocket("/ws/captures")
    async def ws_captures(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            await websocket.send_json({"event_type": "ws.connected", "status": engine.get_status()})
            while True:
                recv = asyncio.create_task(websocket.receive_text())
                done, _ = await asyncio.wait({recv}, timeout=10.0)
                if recv in done:
                    _ = recv.result()
                else:
                    recv.cancel()
                    try:
                        await recv
                    except (asyncio.CancelledError, Exception):
                        pass
                    await websocket.send_json({"event_type": "ws.heartbeat", "status": engine.get_status()})
        except (WebSocketDisconnect, RuntimeError):
            pass

    return router
