"""FastAPI REST & WebSocket routes for JARVIS Module 33 — Defensive Cybersecurity Agent."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import (
    FimBaselineRequest,
    IncidentResolveRequest,
    LogAnalyzeRequest,
    SecretScanRequest,
)
from backend.services.security_engine import CyberSecurityError, DefensiveSecurityEngine

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: CyberSecurityError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: DefensiveSecurityEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/cybersecurity", tags=["JARVIS Module 33 — Defensive Cybersecurity Agent"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-33-defensive-cybersecurity-agent",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.scanner.is_simulated,
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

    @router.post("/scan/secrets", status_code=201)
    async def scan_secrets(body: SecretScanRequest) -> Any:
        try:
            return engine.run_secret_scan(body.relative_path)
        except CyberSecurityError as exc:
            return _err(exc)

    @router.get("/scans")
    async def list_scans() -> Dict[str, Any]:
        scans = engine.db.list_scans()
        return {"scans": scans, "count": len(scans)}

    @router.post("/fim/baseline", status_code=201)
    async def create_baseline(body: FimBaselineRequest) -> Any:
        try:
            return engine.create_fim_baseline(body.name, body.relative_path)
        except CyberSecurityError as exc:
            return _err(exc)

    @router.get("/fim/baselines")
    async def list_baselines() -> Dict[str, Any]:
        bls = engine.db.list_baselines()
        return {"baselines": bls, "count": len(bls)}

    @router.post("/fim/verify/{baseline_id}")
    async def verify_baseline(baseline_id: str) -> Any:
        try:
            return engine.verify_fim_baseline(baseline_id)
        except CyberSecurityError as exc:
            return _err(exc)

    @router.post("/logs/analyze")
    async def analyze_logs(body: LogAnalyzeRequest) -> Dict[str, Any]:
        return engine.analyze_logs(body.source, body.lines)

    @router.get("/incidents")
    async def list_incidents(status_filter: Optional[str] = Query(default=None, alias="status")) -> Dict[str, Any]:
        incs = engine.db.list_incidents(status=status_filter)
        return {"incidents": incs, "count": len(incs)}

    @router.post("/incidents/{incident_id}/resolve")
    async def resolve_incident(incident_id: str, body: IncidentResolveRequest) -> Any:
        try:
            return engine.resolve_incident(incident_id, body.resolution_note)
        except CyberSecurityError as exc:
            return _err(exc)

    @router.websocket("/ws/alerts")
    async def ws_alerts(websocket: WebSocket) -> None:
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
