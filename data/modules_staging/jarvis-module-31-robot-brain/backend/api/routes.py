"""FastAPI REST & WebSocket routes for JARVIS Module 31 — JARVIS Robot Brain."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import (
    EstopRequest,
    EstopResetRequest,
    MissionCreateRequest,
    MotionCommandRequest,
    SensorReadingRequest,
    WaypointCreateRequest,
    model_to_dict,
)
from backend.services.robot_brain_engine import RobotBrainEngine, RobotBrainError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: RobotBrainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: RobotBrainEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/robot-brain", tags=["JARVIS Module 31 — JARVIS Robot Brain"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-31-robot-brain",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.hardware.is_simulated,
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

    @router.post("/estop")
    async def engage_estop(body: EstopRequest) -> Dict[str, Any]:
        return engine.engage_estop(body.reason)

    @router.post("/estop/reset")
    async def reset_estop(body: EstopResetRequest) -> Any:
        try:
            return engine.reset_estop(confirm_reset=body.confirm_reset, operator_note=body.operator_note)
        except RobotBrainError as exc:
            return _err(exc)

    @router.post("/sensors/reading")
    async def sensor_reading(body: SensorReadingRequest) -> Dict[str, Any]:
        return engine.ingest_sensor_reading(model_to_dict(body))

    @router.post("/motion/cmd")
    async def motion_cmd(body: MotionCommandRequest) -> Any:
        try:
            return engine.send_motion_command(body.linear_mps, body.angular_rps, duration_s=body.duration_s)
        except RobotBrainError as exc:
            return _err(exc)

    @router.get("/waypoints")
    async def list_waypoints() -> Dict[str, Any]:
        wps = engine.db.list_waypoints()
        return {"waypoints": wps, "count": len(wps)}

    @router.post("/waypoints", status_code=201)
    async def create_waypoint(body: WaypointCreateRequest) -> Dict[str, Any]:
        return engine.create_waypoint(model_to_dict(body))

    @router.get("/missions")
    async def list_missions() -> Dict[str, Any]:
        ms = engine.db.list_missions()
        return {"missions": ms, "count": len(ms)}

    @router.post("/missions", status_code=201)
    async def create_mission(body: MissionCreateRequest) -> Any:
        try:
            return engine.create_mission(model_to_dict(body))
        except RobotBrainError as exc:
            return _err(exc)

    @router.post("/missions/{mission_id}/execute")
    async def execute_mission(mission_id: str) -> Any:
        try:
            return engine.execute_mission(mission_id)
        except RobotBrainError as exc:
            return _err(exc)

    @router.get("/events")
    async def list_events() -> Dict[str, Any]:
        evts = engine.db.list_events()
        return {"events": evts, "count": len(evts)}

    @router.websocket("/ws/telemetry")
    async def ws_telemetry(websocket: WebSocket) -> None:
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
