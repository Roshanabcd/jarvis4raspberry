"""FastAPI REST & WebSocket routes for JARVIS Module 21."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_21_intelligent_browser_agent.backend.models.database import utc_now_iso
from modules.module_21_intelligent_browser_agent.backend.models.schemas import (
    ApprovalDecisionRequest,
    FormFillRequest,
    FormSubmitRequest,
    NavigateRequest,
    SessionCreateRequest,
    SitePolicyUpdateRequest,
    WorkflowCreateRequest,
    model_to_dict,
)
from modules.module_21_intelligent_browser_agent.backend.services.browser_engine import BrowserAgentError, IntelligentBrowserEngine

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: BrowserAgentError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: IntelligentBrowserEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/browser-agent", tags=["JARVIS Module 21 — Intelligent Browser Agent"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-21-intelligent-browser-agent",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.adapter.is_simulated,
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

    @router.put("/policy")
    async def update_policy(body: SitePolicyUpdateRequest) -> Dict[str, Any]:
        return engine.update_policy(model_to_dict(body))

    # --- Sessions ---
    @router.get("/sessions")
    async def list_sessions() -> Dict[str, Any]:
        s = engine.db.list_sessions()
        return {"sessions": s, "count": len(s)}

    @router.post("/sessions", status_code=201)
    async def create_session(body: SessionCreateRequest) -> Any:
        try:
            return engine.create_session(body.name, body.start_url)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.post("/sessions/{session_id}/close")
    async def close_session(session_id: str) -> Any:
        try:
            return engine.close_session(session_id)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.post("/sessions/{session_id}/navigate")
    async def navigate(session_id: str, body: NavigateRequest) -> Any:
        try:
            return engine.navigate(session_id, body.url)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.get("/sessions/{session_id}/inspect")
    async def inspect(session_id: str) -> Any:
        try:
            return engine.inspect_page(session_id)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.post("/sessions/{session_id}/screenshot")
    async def screenshot(session_id: str) -> Any:
        try:
            return engine.screenshot_and_analyze(session_id)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.post("/sessions/{session_id}/form/fill")
    async def fill_form(session_id: str, body: FormFillRequest) -> Any:
        try:
            return engine.fill_form(session_id, body.form_id, body.fields)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.post("/sessions/{session_id}/form/submit")
    async def submit_form(session_id: str, body: FormSubmitRequest) -> Any:
        try:
            return engine.request_form_submit(session_id, body.form_id, body.fields, requested_by=body.requested_by)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.post("/sessions/{session_id}/download")
    async def download(session_id: str, body: NavigateRequest) -> Any:
        try:
            return engine.download_file(session_id, body.url)
        except BrowserAgentError as exc:
            return _err(exc)

    # --- Workflows & Approvals ---
    @router.get("/workflows")
    async def list_workflows() -> Dict[str, Any]:
        tasks = engine.db.list_tasks()
        return {"workflows": tasks, "count": len(tasks)}

    @router.post("/workflows", status_code=201)
    async def create_workflow(body: WorkflowCreateRequest) -> Any:
        try:
            steps = [model_to_dict(s) for s in body.steps]
            return engine.run_workflow(body.name, steps, session_id=body.session_id, requested_by=body.requested_by)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.post("/workflows/{task_id}/cancel")
    async def cancel_workflow(task_id: str) -> Any:
        try:
            return engine.cancel_workflow(task_id)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.get("/approvals")
    async def list_approvals(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        ap = engine.db.list_approvals(status=status)
        return {"approvals": ap, "count": len(ap)}

    @router.post("/approvals/{approval_id}/decide")
    async def decide_approval(approval_id: str, body: ApprovalDecisionRequest) -> Any:
        try:
            return engine.decide_approval(approval_id, body.approved, body.decided_by, body.comment)
        except BrowserAgentError as exc:
            return _err(exc)

    @router.get("/downloads")
    async def list_downloads() -> Dict[str, Any]:
        d = engine.db.list_downloads()
        return {"downloads": d, "count": len(d)}

    @router.get("/logs")
    async def list_logs(limit: int = Query(default=120, ge=1, le=500)) -> Dict[str, Any]:
        l = engine.db.list_logs(limit=limit)
        return {"logs": l, "count": len(l)}

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
