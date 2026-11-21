"""FastAPI REST & WebSocket routes for JARVIS Module 35 — Visual Workflow Builder."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_35_visual_workflow_builder.backend.models.database import utc_now_iso
from modules.module_35_visual_workflow_builder.backend.models.schemas import WorkflowCreateRequest, WorkflowExecuteRequest, model_to_dict
from modules.module_35_visual_workflow_builder.backend.services.workflow_engine import WorkflowEngine, WorkflowError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: WorkflowError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: WorkflowEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workflows", tags=["JARVIS Module 35 — Visual Workflow Builder"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-35-visual-workflow-builder",
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

    @router.get("/graphs")
    async def list_workflows() -> Dict[str, Any]:
        wfs = engine.db.list_workflows()
        return {"workflows": wfs, "count": len(wfs)}

    @router.post("/graphs", status_code=201)
    async def create_workflow(body: WorkflowCreateRequest) -> Any:
        try:
            return engine.create_workflow(model_to_dict(body))
        except WorkflowError as exc:
            return _err(exc)

    @router.post("/graphs/{workflow_id}/validate")
    async def validate_workflow(workflow_id: str) -> Any:
        try:
            return engine.validate_workflow_by_id(workflow_id)
        except WorkflowError as exc:
            return _err(exc)

    @router.post("/graphs/{workflow_id}/execute", status_code=201)
    async def execute_workflow(workflow_id: str, body: WorkflowExecuteRequest) -> Any:
        try:
            return engine.execute_workflow(workflow_id, body.input_data)
        except WorkflowError as exc:
            return _err(exc)

    @router.get("/runs")
    async def list_runs(workflow_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        runs = engine.db.list_runs(workflow_id=workflow_id)
        return {"runs": runs, "count": len(runs)}

    @router.websocket("/ws/runs")
    async def ws_runs(websocket: WebSocket) -> None:
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
