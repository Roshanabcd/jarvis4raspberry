"""FastAPI REST & WebSocket routes for JARVIS Module 26 — Project Autopilot."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse

from modules.module_26_project_autopilot.backend.models.database import utc_now_iso
from modules.module_26_project_autopilot.backend.models.schemas import (
    AdvanceProjectRequest,
    ApprovalDecisionRequest,
    ProjectCreateRequest,
    ScaffoldRequest,
    TaskCreateRequest,
    model_to_dict,
)
from modules.module_26_project_autopilot.backend.services.autopilot_engine import AutopilotError, ProjectAutopilotEngine

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: AutopilotError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: ProjectAutopilotEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/project-autopilot", tags=["JARVIS Module 26 — Project Autopilot"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-26-project-autopilot",
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

    @router.get("/projects")
    async def list_projects() -> Dict[str, Any]:
        projs = engine.db.list_projects()
        return {"projects": projs, "count": len(projs)}

    @router.post("/projects", status_code=201)
    async def create_project(body: ProjectCreateRequest) -> Dict[str, Any]:
        return engine.create_project(model_to_dict(body))

    @router.get("/projects/{project_id}")
    async def get_project(project_id: str) -> Any:
        try:
            return engine.get_project_bundle(project_id)
        except AutopilotError as exc:
            return _err(exc)

    @router.post("/projects/{project_id}/tasks", status_code=201)
    async def add_task(project_id: str, body: TaskCreateRequest) -> Any:
        try:
            return engine.add_task(project_id, model_to_dict(body))
        except AutopilotError as exc:
            return _err(exc)

    @router.post("/projects/{project_id}/advance")
    async def advance_project(project_id: str, body: AdvanceProjectRequest) -> Any:
        try:
            return engine.advance_project(project_id, max_steps=body.max_steps, dry_run=body.dry_run)
        except AutopilotError as exc:
            return _err(exc)

    @router.post("/projects/{project_id}/scaffold", status_code=201)
    async def scaffold_workspace(project_id: str, body: ScaffoldRequest) -> Any:
        try:
            return engine.scaffold_workspace(project_id, include_tests=body.include_tests)
        except AutopilotError as exc:
            return _err(exc)

    @router.get("/projects/{project_id}/blueprint.md")
    async def export_blueprint(project_id: str) -> Any:
        try:
            md = engine.export_blueprint_markdown(project_id)
            return PlainTextResponse(content=md, media_type="text/markdown")
        except AutopilotError as exc:
            return _err(exc)

    @router.get("/approvals")
    async def list_approvals(project_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        items = engine.db.list_tasks(project_id=project_id, status="awaiting_approval")
        return {"approvals": items, "count": len(items)}

    @router.post("/tasks/{task_id}/approval")
    async def decide_approval(task_id: str, body: ApprovalDecisionRequest) -> Any:
        try:
            return engine.decide_approval(task_id, decision=body.decision, reviewer=body.reviewer, note=body.note)
        except AutopilotError as exc:
            return _err(exc)

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
