"""FastAPI REST & WebSocket routes for JARVIS Module 19."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import (
    ActionExecuteRequest,
    ApprovalDecisionRequest,
    DryRunToggleRequest,
    EstopRequest,
    PermissionPolicyUpdateRequest,
    ReplayRequest,
    model_to_dict,
)
from backend.services.assistant_engine import AssistantError, ComputerAssistantEngine

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _error_response(exc: AssistantError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": utc_now_iso(),
            }
        },
    )


def build_router(engine: ComputerAssistantEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/computer-assistant", tags=["JARVIS Module 19 — Autonomous Computer Assistant"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-19-autonomous-computer-assistant",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "adapter_simulated": engine.adapter.is_simulated,
            "estop_active": engine.estop_active,
            "dry_run_mode": engine.dry_run_mode,
            "timestamp": utc_now_iso(),
        }

    @router.get("/manifest")
    async def get_manifest() -> Dict[str, Any]:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="manifest.json not found")

    @router.get("/status")
    async def get_status() -> Dict[str, Any]:
        return engine.get_status()

    @router.get("/diagnostics")
    async def get_diagnostics() -> Dict[str, Any]:
        return engine.get_diagnostics()

    # --- Desktop Discovery & State ---
    @router.get("/apps")
    async def discover_apps() -> Dict[str, Any]:
        apps = engine.adapter.discover_applications()
        return {"simulated": engine.adapter.is_simulated, "apps": apps, "count": len(apps)}

    @router.get("/windows")
    async def list_windows() -> Dict[str, Any]:
        windows = engine.adapter.list_windows()
        return {"simulated": engine.adapter.is_simulated, "windows": windows, "count": len(windows)}

    @router.get("/screenshots")
    async def list_screenshots(limit: int = Query(default=20, ge=1, le=100)) -> Dict[str, Any]:
        shots = engine.db.list_screenshots(limit=limit)
        return {"screenshots": shots, "count": len(shots)}

    @router.get("/screenshots/{screenshot_id}")
    async def get_screenshot(screenshot_id: str) -> Any:
        shot = engine.db.get_screenshot(screenshot_id)
        if not shot:
            return _error_response(AssistantError("SCREENSHOT_NOT_FOUND", f"Screenshot '{screenshot_id}' not found", 404))
        return shot

    # --- Safety Controls ---
    @router.post("/safety/estop")
    async def engage_estop(body: EstopRequest) -> Dict[str, Any]:
        return engine.engage_estop(reason=body.reason, triggered_by=body.triggered_by)

    @router.post("/safety/estop/reset")
    async def reset_estop(reset_by: str = Query(default="operator")) -> Dict[str, Any]:
        return engine.reset_estop(reset_by=reset_by)

    @router.put("/safety/dry-run")
    async def toggle_dry_run(body: DryRunToggleRequest) -> Dict[str, Any]:
        return engine.set_dry_run(body.enabled)

    @router.put("/safety/policy")
    async def update_policy(body: PermissionPolicyUpdateRequest) -> Dict[str, bool]:
        return engine.update_policy(model_to_dict(body))

    # --- Actions, Approvals, Replay ---
    @router.get("/actions")
    async def list_actions(status: Optional[str] = Query(default=None), limit: int = Query(default=100, ge=1, le=500)) -> Dict[str, Any]:
        actions = engine.db.list_actions(status=status, limit=limit)
        return {"actions": actions, "count": len(actions)}

    @router.post("/actions", status_code=201)
    async def execute_action(body: ActionExecuteRequest) -> Any:
        try:
            return engine.submit_action(
                action_type=body.action_type.value,
                params=body.params,
                dry_run=body.dry_run,
                requested_by=body.requested_by,
                reason=body.reason,
            )
        except AssistantError as exc:
            return _error_response(exc)

    @router.post("/actions/replay", status_code=201)
    async def replay_actions(body: ReplayRequest) -> Any:
        try:
            return engine.replay_actions(body.action_ids, dry_run=body.dry_run, requested_by=body.requested_by)
        except AssistantError as exc:
            return _error_response(exc)

    @router.get("/approvals")
    async def list_approvals(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        approvals = engine.db.list_approvals(status=status)
        return {"approvals": approvals, "count": len(approvals)}

    @router.post("/approvals/{approval_id}/decide")
    async def decide_approval(approval_id: str, body: ApprovalDecisionRequest) -> Any:
        try:
            return engine.decide_approval(
                approval_id=approval_id,
                approved=body.approved,
                decided_by=body.decided_by,
                comment=body.comment,
            )
        except AssistantError as exc:
            return _error_response(exc)

    @router.get("/logs")
    async def list_logs(limit: int = Query(default=120, ge=1, le=500)) -> Dict[str, Any]:
        logs = engine.db.list_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}

    @router.websocket("/ws/events")
    async def ws_events(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            await websocket.send_json({"event_type": "ws.connected", "status": engine.get_status()})
            while True:
                recv_task = asyncio.create_task(websocket.receive_text())
                done, pending = await asyncio.wait({recv_task}, timeout=10.0)
                if recv_task in done:
                    _ = recv_task.result()
                else:
                    recv_task.cancel()
                    try:
                        await recv_task
                    except (asyncio.CancelledError, Exception):
                        pass
                    await websocket.send_json({"event_type": "ws.heartbeat", "status": engine.get_status()})
        except (WebSocketDisconnect, RuntimeError):
            pass

    return router
