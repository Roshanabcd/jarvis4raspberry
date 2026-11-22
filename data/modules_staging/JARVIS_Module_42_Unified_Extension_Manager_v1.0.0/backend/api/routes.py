"""FastAPI REST & WebSocket routes for JARVIS Module 42 — Unified Extension Manager."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.schemas import (
    ApprovalCreateRequest,
    ApprovalDecisionRequest,
    EventPublishRequest,
    InstallPlanRequest,
    ModuleConfigUpdateRequest,
    ModuleRegisterRequest,
    ModuleToggleRequest,
    ScanFolderRequest,
    model_to_dict,
)
from backend.services.extension_manager import ExtensionManager, ExtensionManagerError
from sdk.jarvis_sdk.contracts import CONTRACT_VERSION, SDK_VERSION, utc_now_iso

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: ExtensionManagerError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(manager: ExtensionManager) -> APIRouter:
    router = APIRouter(prefix="/api/v1/extensions", tags=["JARVIS Module 42 — Unified Extension Manager"])

    def require_auth(x_jarvis_token: Optional[str] = Header(default=None)) -> None:
        expected = manager.config.api_token
        if expected and x_jarvis_token != expected:
            raise HTTPException(
                status_code=401,
                detail={"code": "UNAUTHORIZED", "message": "Valid X-JARVIS-Token header required."},
            )

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-42-unified-extension-manager",
            "version": "1.0.0",
            "contract_version": CONTRACT_VERSION,
            "sdk_version": SDK_VERSION,
            "simulated": manager.is_simulated,
            "timestamp": utc_now_iso(),
        }

    @router.get("/manifest")
    async def manifest() -> Dict[str, Any]:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="manifest.json not found")

    @router.get("/status")
    async def status() -> Dict[str, Any]:
        return manager.get_status()

    # --- Archive Scanner & Compatibility ---
    @router.post("/scan", dependencies=[Depends(require_auth)])
    async def scan_folder(body: ScanFolderRequest) -> Any:
        try:
            return manager.scan_folder(
                folder_path=body.folder_path,
                register_discovered=body.register_discovered,
                target_arch=body.target_arch,
            )
        except ExtensionManagerError as exc:
            return _err(exc)

    @router.get("/compatibility/conflicts")
    async def compatibility_conflicts() -> Dict[str, Any]:
        conflicts = manager.analyzer.detect_cross_module_conflicts(manager.db.list_modules())
        return {"conflicts": conflicts, "count": len(conflicts)}

    # --- Module Registry ---
    @router.get("/modules")
    async def list_modules(enabled: Optional[bool] = Query(default=None)) -> Dict[str, Any]:
        mods = manager.db.list_modules(enabled=enabled)
        return {"modules": mods, "count": len(mods)}

    @router.post("/modules", status_code=201, dependencies=[Depends(require_auth)])
    async def register_module(body: ModuleRegisterRequest) -> Dict[str, Any]:
        return manager.register_module(model_to_dict(body))

    @router.get("/modules/{module_id}")
    async def get_module(module_id: str) -> Any:
        mod = manager.db.get_module(module_id)
        if not mod:
            return _err(ExtensionManagerError("MODULE_NOT_FOUND", f"Module '{module_id}' not found.", 404))
        return mod

    @router.post("/modules/{module_id}/toggle", dependencies=[Depends(require_auth)])
    async def toggle_module(module_id: str, body: ModuleToggleRequest) -> Any:
        try:
            return manager.toggle_module(module_id, body.enabled)
        except ExtensionManagerError as exc:
            return _err(exc)

    @router.put("/modules/{module_id}/config", dependencies=[Depends(require_auth)])
    async def update_module_config(module_id: str, body: ModuleConfigUpdateRequest) -> Any:
        try:
            return manager.update_module_config(
                module_id=module_id,
                config=body.config,
                health_endpoint=body.health_endpoint,
                installed_location=body.installed_location,
            )
        except ExtensionManagerError as exc:
            return _err(exc)

    @router.post("/modules/{module_id}/health-check", dependencies=[Depends(require_auth)])
    async def probe_module_health(module_id: str) -> Dict[str, Any]:
        return await manager.probe_health(module_id)

    # --- Dry-Run Install Planner & Approvals ---
    @router.post("/plan")
    async def build_install_plan(body: InstallPlanRequest) -> Dict[str, Any]:
        return manager.build_install_plan(module_ids=body.module_ids)

    @router.get("/approvals")
    async def list_approvals(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        items = manager.db.list_approvals(status=status)
        return {"approvals": items, "count": len(items)}

    @router.post("/approvals", status_code=201, dependencies=[Depends(require_auth)])
    async def create_approval(body: ApprovalCreateRequest) -> Dict[str, Any]:
        return manager.create_approval(body.module_id, body.action, body.summary, body.requested_by)

    @router.post("/approvals/{request_id}/decide", dependencies=[Depends(require_auth)])
    async def decide_approval(request_id: str, body: ApprovalDecisionRequest) -> Any:
        try:
            return manager.decide_approval(request_id, body.decision, body.reviewer, body.notes)
        except ExtensionManagerError as exc:
            return _err(exc)

    # --- Shared Event Bus & Logs ---
    @router.post("/events/publish", status_code=201, dependencies=[Depends(require_auth)])
    async def publish_event(body: EventPublishRequest) -> Dict[str, Any]:
        return await manager.publish_event(body.event_type, body.source_module, body.payload, body.correlation_id)

    @router.get("/events")
    async def list_events(limit: int = Query(default=100, ge=1, le=500)) -> Dict[str, Any]:
        events = manager.db.list_events(limit=limit)
        return {"events": events, "dead_letters": manager.event_bus.get_dead_letters(limit=50), "count": len(events)}

    @router.get("/logs")
    async def list_logs(limit: int = Query(default=100, ge=1, le=500)) -> Dict[str, Any]:
        logs = manager.db.list_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}

    @router.websocket("/ws/events")
    async def ws_events(websocket: WebSocket) -> None:
        await websocket.accept()
        queue = manager.subscribe_ws()
        try:
            await websocket.send_json({"event_type": "ws.connected", "status": manager.get_status()})
            while True:
                recv_task = asyncio.create_task(websocket.receive_text())
                evt_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait({recv_task, evt_task}, timeout=10.0, return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
                    try:
                        await p
                    except (asyncio.CancelledError, Exception):
                        pass
                if recv_task in done:
                    _ = recv_task.result()
                elif evt_task in done:
                    await websocket.send_json(evt_task.result())
                else:
                    await websocket.send_json({"event_type": "ws.heartbeat", "status": manager.get_status()})
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            manager.unsubscribe_ws(queue)

    return router
