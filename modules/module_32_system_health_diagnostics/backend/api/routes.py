"""FastAPI REST & WebSocket routes for JARVIS Module 32 — System Health & Diagnostics."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_32_system_health_diagnostics.backend.models.database import utc_now_iso
from modules.module_32_system_health_diagnostics.backend.models.schemas import AlertRuleCreateRequest, ServiceCheckCreateRequest, model_to_dict
from modules.module_32_system_health_diagnostics.backend.services.health_engine import SystemHealthEngine, SystemHealthError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: SystemHealthError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: SystemHealthEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/system-health", tags=["JARVIS Module 32 — System Health & Diagnostics"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-32-system-health-diagnostics",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.probe.is_simulated,
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

    @router.get("/metrics")
    async def live_metrics() -> Dict[str, Any]:
        return {"metrics": engine.get_live_metrics(), "simulated": engine.probe.is_simulated}

    @router.post("/snapshots/capture", status_code=201)
    async def capture_snapshot() -> Dict[str, Any]:
        return engine.capture_snapshot()

    @router.get("/snapshots")
    async def list_snapshots() -> Dict[str, Any]:
        snaps = engine.db.list_snapshots()
        return {"snapshots": snaps, "count": len(snaps)}

    @router.get("/rules")
    async def list_rules() -> Dict[str, Any]:
        rules = engine.db.list_rules()
        return {"rules": rules, "count": len(rules)}

    @router.post("/rules", status_code=201)
    async def create_rule(body: AlertRuleCreateRequest) -> Dict[str, Any]:
        return engine.create_rule(model_to_dict(body))

    @router.get("/alerts")
    async def list_alerts(unacknowledged_only: bool = Query(default=False)) -> Dict[str, Any]:
        alerts = engine.db.list_alerts(unacknowledged_only=unacknowledged_only)
        return {"alerts": alerts, "count": len(alerts)}

    @router.post("/alerts/{alert_id}/ack")
    async def ack_alert(alert_id: str) -> Any:
        try:
            return engine.ack_alert(alert_id)
        except SystemHealthError as exc:
            return _err(exc)

    @router.get("/services")
    async def list_services() -> Dict[str, Any]:
        svcs = engine.db.list_services()
        return {"services": svcs, "count": len(svcs)}

    @router.post("/services", status_code=201)
    async def register_service(body: ServiceCheckCreateRequest) -> Any:
        try:
            return engine.register_service(model_to_dict(body))
        except SystemHealthError as exc:
            return _err(exc)

    @router.post("/services/probe")
    async def probe_services() -> Dict[str, Any]:
        return engine.probe_all_services()

    @router.post("/diagnostics/run", status_code=201)
    async def run_diagnostics() -> Dict[str, Any]:
        return engine.run_diagnostics()

    @router.get("/diagnostics")
    async def list_diagnostics() -> Dict[str, Any]:
        runs = engine.db.list_diagnostic_runs()
        return {"diagnostics": runs, "count": len(runs)}

    @router.websocket("/ws/metrics")
    async def ws_metrics(websocket: WebSocket) -> None:
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
