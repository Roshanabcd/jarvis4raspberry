"""FastAPI REST & WebSocket routes for JARVIS Module 41 — Universal Notification Center."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import NotificationCreateRequest, PreferencesUpdateRequest, model_to_dict
from backend.services.notification_engine import NotificationEngine, NotificationError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: NotificationError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: NotificationEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/notifications", tags=["JARVIS Module 41 — Universal Notification Center"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-41-universal-notification-center",
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

    @router.get("/preferences")
    async def get_preferences() -> Dict[str, Any]:
        return engine.db.get_preferences()

    @router.put("/preferences")
    async def update_preferences(body: PreferencesUpdateRequest) -> Any:
        try:
            return engine.update_preferences(
                dnd_enabled=body.dnd_enabled,
                allow_critical_during_dnd=body.allow_critical_during_dnd,
                enabled_channels=body.enabled_channels,
            )
        except NotificationError as exc:
            return _err(exc)

    @router.get("/items")
    async def list_items(
        status: Optional[str] = Query(default=None),
        priority: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        items = engine.db.list_notifications(status=status, priority=priority)
        return {"notifications": items, "count": len(items)}

    @router.post("/items", status_code=201)
    async def send_item(body: NotificationCreateRequest) -> Any:
        try:
            return engine.send_notification(model_to_dict(body))
        except NotificationError as exc:
            return _err(exc)

    @router.post("/items/{notification_id}/ack")
    async def ack_item(notification_id: str) -> Any:
        try:
            return engine.acknowledge(notification_id)
        except NotificationError as exc:
            return _err(exc)

    @router.post("/items/{notification_id}/dismiss")
    async def dismiss_item(notification_id: str) -> Any:
        try:
            return engine.dismiss(notification_id)
        except NotificationError as exc:
            return _err(exc)

    @router.websocket("/ws/stream")
    async def ws_stream(websocket: WebSocket) -> None:
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
