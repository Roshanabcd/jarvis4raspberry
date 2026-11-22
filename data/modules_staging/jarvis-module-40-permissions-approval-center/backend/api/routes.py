"""FastAPI REST & WebSocket routes for JARVIS Module 40 — Permissions & Approval Center."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import ApprovalDecisionRequest, ApprovalSubmitRequest, PolicyUpsertRequest, model_to_dict
from backend.services.approval_engine import ApprovalEngine, ApprovalError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: ApprovalError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: ApprovalEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/approvals", tags=["JARVIS Module 40 — Permissions & Approval Center"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-40-permissions-approval-center",
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

    @router.get("/policies")
    async def list_policies() -> Dict[str, Any]:
        items = engine.db.list_policies()
        return {"policies": items, "count": len(items)}

    @router.post("/policies", status_code=201)
    async def upsert_policy(body: PolicyUpsertRequest) -> Any:
        try:
            return engine.upsert_policy(model_to_dict(body))
        except ApprovalError as exc:
            return _err(exc)

    @router.get("/requests")
    async def list_requests(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        items = engine.db.list_requests(status=status)
        return {"requests": items, "count": len(items)}

    @router.post("/requests", status_code=201)
    async def submit_request(body: ApprovalSubmitRequest) -> Any:
        try:
            return engine.submit_request(model_to_dict(body))
        except ApprovalError as exc:
            return _err(exc)

    @router.post("/requests/{request_id}/decide")
    async def decide_request(request_id: str, body: ApprovalDecisionRequest) -> Any:
        try:
            return engine.decide_request(request_id, body.decision, body.reviewer, body.rationale)
        except ApprovalError as exc:
            return _err(exc)

    @router.get("/audit")
    async def list_audit() -> Dict[str, Any]:
        items = engine.db.list_audit()
        return {"events": items, "count": len(items)}

    @router.websocket("/ws/requests")
    async def ws_requests(websocket: WebSocket) -> None:
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
