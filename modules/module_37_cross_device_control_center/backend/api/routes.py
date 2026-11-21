"""FastAPI REST & WebSocket routes for JARVIS Module 37 — Cross-Device Control Center."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_37_cross_device_control_center.backend.models.database import utc_now_iso
from modules.module_37_cross_device_control_center.backend.models.schemas import (
    ClipboardSyncRequest,
    DeviceCommandRequest,
    DeviceHeartbeatRequest,
    DeviceRegisterRequest,
    model_to_dict,
)
from modules.module_37_cross_device_control_center.backend.services.device_mesh_engine import DeviceMeshEngine, DeviceMeshError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: DeviceMeshError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: DeviceMeshEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/devices", tags=["JARVIS Module 37 — Cross-Device Control Center"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-37-cross-device-control-center",
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

    @router.get("/nodes")
    async def list_devices() -> Dict[str, Any]:
        devices = engine.db.list_devices()
        return {"devices": devices, "count": len(devices)}

    @router.post("/nodes", status_code=201)
    async def register_device(body: DeviceRegisterRequest) -> Any:
        try:
            return engine.register_device(model_to_dict(body))
        except DeviceMeshError as exc:
            return _err(exc)

    @router.post("/nodes/{device_id}/heartbeat")
    async def heartbeat(device_id: str, body: DeviceHeartbeatRequest) -> Any:
        try:
            return engine.heartbeat(device_id, online=body.online, battery_pct=body.battery_pct)
        except DeviceMeshError as exc:
            return _err(exc)

    @router.post("/nodes/{device_id}/commands", status_code=201)
    async def dispatch_command(device_id: str, body: DeviceCommandRequest) -> Any:
        try:
            return engine.dispatch_command(device_id, body.capability, body.action, body.params)
        except DeviceMeshError as exc:
            return _err(exc)

    @router.get("/commands")
    async def list_commands(device_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        cmds = engine.db.list_commands(device_id=device_id)
        return {"commands": cmds, "count": len(cmds)}

    @router.get("/clipboard")
    async def list_clipboard() -> Dict[str, Any]:
        entries = engine.db.list_clipboard()
        return {"entries": entries, "count": len(entries)}

    @router.post("/clipboard", status_code=201)
    async def sync_clipboard(body: ClipboardSyncRequest) -> Any:
        try:
            return engine.sync_clipboard(body.source_device_id, body.content, body.mime_type)
        except DeviceMeshError as exc:
            return _err(exc)

    @router.websocket("/ws/mesh")
    async def ws_mesh(websocket: WebSocket) -> None:
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
