"""FastAPI REST & WebSocket routes for JARVIS Module 25 — AI Meeting Assistant."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse

from modules.module_25_ai_meeting_assistant.backend.models.database import utc_now_iso
from modules.module_25_ai_meeting_assistant.backend.models.schemas import (
    ActionItemStatusRequest,
    BulkTranscriptRequest,
    MeetingCreateRequest,
    TranscriptSegmentRequest,
    model_to_dict,
)
from modules.module_25_ai_meeting_assistant.backend.services.meeting_engine import MeetingAssistantEngine, MeetingAssistantError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: MeetingAssistantError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: MeetingAssistantEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/meeting-assistant", tags=["JARVIS Module 25 — AI Meeting Assistant"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-25-ai-meeting-assistant",
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

    @router.get("/meetings")
    async def list_meetings() -> Dict[str, Any]:
        m = engine.db.list_meetings()
        return {"meetings": m, "count": len(m)}

    @router.post("/meetings", status_code=201)
    async def create_meeting(body: MeetingCreateRequest) -> Dict[str, Any]:
        return engine.create_meeting(model_to_dict(body))

    @router.get("/meetings/{meeting_id}")
    async def get_meeting(meeting_id: str) -> Any:
        m = engine.db.get_meeting(meeting_id)
        if not m:
            return _err(MeetingAssistantError("MEETING_NOT_FOUND", f"Meeting '{meeting_id}' not found.", 404))
        return {
            "meeting": m,
            "segments": engine.db.list_segments(meeting_id),
            "action_items": engine.db.list_action_items(meeting_id=meeting_id),
        }

    @router.post("/meetings/{meeting_id}/transcript", status_code=201)
    async def add_segment(meeting_id: str, body: TranscriptSegmentRequest) -> Any:
        try:
            return engine.add_segment(meeting_id, body.speaker, body.text, body.timestamp_sec)
        except MeetingAssistantError as exc:
            return _err(exc)

    @router.post("/meetings/{meeting_id}/transcript/bulk", status_code=201)
    async def bulk_transcript(meeting_id: str, body: BulkTranscriptRequest) -> Any:
        try:
            return engine.ingest_bulk_transcript(meeting_id, body.raw_transcript)
        except MeetingAssistantError as exc:
            return _err(exc)

    @router.post("/meetings/{meeting_id}/analyze")
    async def analyze_meeting(meeting_id: str) -> Any:
        try:
            return engine.analyze_meeting(meeting_id)
        except MeetingAssistantError as exc:
            return _err(exc)

    @router.get("/meetings/{meeting_id}/minutes.md")
    async def export_minutes(meeting_id: str) -> Any:
        try:
            md = engine.export_markdown_minutes(meeting_id)
            return PlainTextResponse(content=md, media_type="text/markdown")
        except MeetingAssistantError as exc:
            return _err(exc)

    @router.get("/action-items")
    async def list_action_items(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        items = engine.db.list_action_items(status=status)
        return {"action_items": items, "count": len(items)}

    @router.patch("/action-items/{item_id}")
    async def update_action_item(item_id: str, body: ActionItemStatusRequest) -> Any:
        try:
            return engine.update_action_item(item_id, body.status)
        except MeetingAssistantError as exc:
            return _err(exc)

    @router.get("/search")
    async def search(q: str = Query(..., min_length=1)) -> Dict[str, Any]:
        hits = engine.db.search_transcripts(q)
        return {"query": q, "results": hits, "count": len(hits)}

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
