"""FastAPI REST & WebSocket routes for JARVIS Module 28 — AI Data Analyst."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import (
    AggregateRequest,
    AnomalyRequest,
    DatasetCSVRequest,
    DatasetRowsRequest,
    QuestionRequest,
)
from backend.services.analyst_engine import DataAnalystEngine, DataAnalystError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: DataAnalystError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: DataAnalystEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ai-data-analyst", tags=["JARVIS Module 28 — AI Data Analyst"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-28-ai-data-analyst",
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

    @router.get("/datasets")
    async def list_datasets() -> Dict[str, Any]:
        items = engine.db.list_datasets()
        return {"datasets": items, "count": len(items)}

    @router.post("/datasets/csv", status_code=201)
    async def ingest_csv(body: DatasetCSVRequest) -> Any:
        try:
            return engine.ingest_csv(name=body.name, csv_text=body.csv_text, description=body.description)
        except DataAnalystError as exc:
            return _err(exc)

    @router.post("/datasets/rows", status_code=201)
    async def ingest_rows(body: DatasetRowsRequest) -> Any:
        try:
            return engine.ingest_rows(name=body.name, rows=body.rows, description=body.description)
        except DataAnalystError as exc:
            return _err(exc)

    @router.get("/datasets/{dataset_id}")
    async def get_dataset(dataset_id: str) -> Any:
        ds = engine.db.get_dataset(dataset_id, include_rows=True)
        if not ds:
            return _err(DataAnalystError("DATASET_NOT_FOUND", f"Dataset '{dataset_id}' not found.", 404))
        return {"dataset": ds, "queries": engine.db.list_queries(dataset_id=dataset_id)}

    @router.post("/datasets/{dataset_id}/aggregate")
    async def aggregate(dataset_id: str, body: AggregateRequest) -> Any:
        try:
            return engine.aggregate(dataset_id, group_by=body.group_by, metric=body.metric, agg=body.agg)
        except DataAnalystError as exc:
            return _err(exc)

    @router.post("/datasets/{dataset_id}/anomalies")
    async def anomalies(dataset_id: str, body: AnomalyRequest) -> Any:
        try:
            return engine.detect_anomalies(dataset_id, column=body.column, z_threshold=body.z_threshold)
        except DataAnalystError as exc:
            return _err(exc)

    @router.post("/datasets/{dataset_id}/ask")
    async def ask(dataset_id: str, body: QuestionRequest) -> Any:
        try:
            return engine.ask_question(dataset_id, question=body.question)
        except DataAnalystError as exc:
            return _err(exc)

    @router.get("/datasets/{dataset_id}/report.md")
    async def export_report(dataset_id: str) -> Any:
        try:
            md = engine.export_markdown_report(dataset_id)
            return PlainTextResponse(content=md, media_type="text/markdown")
        except DataAnalystError as exc:
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
