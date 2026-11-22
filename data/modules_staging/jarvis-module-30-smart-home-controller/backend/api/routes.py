"""FastAPI REST & WebSocket routes for JARVIS Module 30 — Smart Home Controller."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import (
    DeviceCommandRequest,
    DeviceCreateRequest,
    RuleCreateRequest,
    SceneCreateRequest,
    model_to_dict,
)
from backend.services.smart_home_engine import SmartHomeEngine, SmartHomeError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: SmartHomeError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: SmartHomeEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/smart-home", tags=["JARVIS Module 30 — Smart Home Controller"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-30-smart-home-controller",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.bridge.is_simulated,
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

    @router.get("/devices")
    async def list_devices(room: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        devs = engine.db.list_devices(room=room)
        return {"devices": devs, "count": len(devs)}

    @router.post("/devices", status_code=201)
    async def register_device(body: DeviceCreateRequest) -> Dict[str, Any]:
        return engine.register_device(model_to_dict(body))

    @router.post("/devices/{device_id}/command")
    async def send_command(device_id: str, body: DeviceCommandRequest) -> Any:
        try:
            return engine.send_command(device_id, body.command, value=body.value, confirm_unlock=body.confirm_unlock)
        except SmartHomeError as exc:
            return _err(exc)

    @router.get("/scenes")
    async def list_scenes() -> Dict[str, Any]:
        scenes = engine.db.list_scenes()
        return {"scenes": scenes, "count": len(scenes)}

    @router.post("/scenes", status_code=201)
    async def create_scene(body: SceneCreateRequest) -> Any:
        try:
            return engine.create_scene(model_to_dict(body))
        except SmartHomeError as exc:
            return _err(exc)

    @router.post("/scenes/{scene_id}/activate")
    async def activate_scene(scene_id: str) -> Any:
        try:
            return engine.activate_scene(scene_id)
        except SmartHomeError as exc:
            return _err(exc)

    @router.get("/rules")
    async def list_rules() -> Dict[str, Any]:
        rules = engine.db.list_rules()
        return {"rules": rules, "count": len(rules)}

    @router.post("/rules", status_code=201)
    async def create_rule(body: RuleCreateRequest) -> Any:
        try:
            return engine.create_rule(model_to_dict(body))
        except SmartHomeError as exc:
            return _err(exc)

    @router.post("/rules/evaluate")
    async def evaluate_rules() -> Dict[str, Any]:
        return engine.evaluate_rules()

    @router.get("/energy")
    async def energy() -> Dict[str, Any]:
        return engine.get_energy_summary()

    @router.get("/events")
    async def events() -> Dict[str, Any]:
        evts = engine.db.list_events()
        return {"events": evts, "count": len(evts)}

    @router.websocket("/ws/events")
    async def ws_events(websocket: WebSocket) -> None:
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
