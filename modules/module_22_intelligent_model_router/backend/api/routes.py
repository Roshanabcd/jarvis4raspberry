"""FastAPI REST & WebSocket routes for JARVIS Module 22 — Intelligent AI Model Router."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_22_intelligent_model_router.backend.models.database import utc_now_iso
from modules.module_22_intelligent_model_router.backend.models.schemas import (
    BenchmarkRequest,
    BudgetUpdateRequest,
    ModelRegisterRequest,
    ModelToggleRequest,
    RouteRequest,
    model_to_dict,
)
from modules.module_22_intelligent_model_router.backend.services.router_engine import IntelligentModelRouterEngine, ModelRouterError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: ModelRouterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: IntelligentModelRouterEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/model-router", tags=["JARVIS Module 22 — Intelligent AI Model Router"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-22-intelligent-model-router",
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

    @router.get("/models")
    async def list_models() -> Dict[str, Any]:
        models = engine.db.list_models()
        return {"models": models, "count": len(models)}

    @router.post("/models", status_code=201)
    async def register_model(body: ModelRegisterRequest) -> Dict[str, Any]:
        return engine.register_model(model_to_dict(body))

    @router.patch("/models/{model_id}")
    async def toggle_model(model_id: str, body: ModelToggleRequest) -> Any:
        try:
            return engine.toggle_model(
                model_id,
                enabled=body.enabled,
                simulate_outage=body.simulate_outage,
                reset_circuit=body.reset_circuit,
            )
        except ModelRouterError as exc:
            return _err(exc)

    @router.post("/route")
    async def route_prompt(body: RouteRequest) -> Any:
        try:
            return engine.route_request(
                body.prompt,
                task_type=body.task_type,
                strategy=body.strategy,
                max_cost_usd=body.max_cost_usd,
                require_local=body.require_local,
                use_cache=body.use_cache,
                preferred_model_id=body.preferred_model_id,
            )
        except ModelRouterError as exc:
            return _err(exc)

    @router.post("/benchmark")
    async def benchmark(body: BenchmarkRequest) -> Dict[str, Any]:
        return engine.run_benchmark(body.prompt, body.model_ids, task_type=body.task_type)

    @router.put("/budget")
    async def update_budget(body: BudgetUpdateRequest) -> Dict[str, Any]:
        return engine.update_budget_policy(model_to_dict(body))

    @router.post("/cache/clear")
    async def clear_cache() -> Dict[str, Any]:
        cleared = engine.db.clear_cache()
        return {"cleared_entries": cleared}

    @router.get("/logs")
    async def list_logs(limit: int = Query(default=60, ge=1, le=500)) -> Dict[str, Any]:
        logs = engine.db.list_routing_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}

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
