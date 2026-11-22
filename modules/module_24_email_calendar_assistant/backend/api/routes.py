"""FastAPI REST & WebSocket routes for JARVIS Module 24 — Email & Calendar Assistant."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse

from modules.module_24_email_calendar_assistant.backend.models.database import utc_now_iso
from modules.module_24_email_calendar_assistant.backend.models.schemas import (
    ApprovalDecisionRequest,
    CalendarEventCreateRequest,
    CalendarRsvpRequest,
    DraftCreateRequest,
    DraftReplyOptions,
    EmailIngestRequest,
    FreeSlotsRequest,
    model_to_dict,
)
from modules.module_24_email_calendar_assistant.backend.services.email_calendar_engine import EmailCalendarEngine, EmailCalendarError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: EmailCalendarError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: EmailCalendarEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/email-calendar", tags=["JARVIS Module 24 — Email & Calendar Assistant"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-24-email-calendar-assistant",
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

    # --- Emails ---
    @router.get("/emails")
    async def list_emails(category: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        em = engine.db.list_emails(category=category)
        return {"emails": em, "count": len(em)}

    @router.post("/emails", status_code=201)
    async def ingest_email(body: EmailIngestRequest) -> Dict[str, Any]:
        return engine.ingest_email(model_to_dict(body))

    @router.post("/emails/{email_id}/draft-reply", status_code=201)
    async def draft_reply(email_id: str, body: DraftReplyOptions) -> Any:
        try:
            return engine.draft_reply(email_id, tone=body.tone, extra_notes=body.extra_notes)
        except EmailCalendarError as exc:
            return _err(exc)

    @router.post("/emails/{email_id}/archive")
    async def archive_email(email_id: str) -> Any:
        res = engine.db.mark_email(email_id, is_read=True, archived=True)
        if not res:
            return _err(EmailCalendarError("EMAIL_NOT_FOUND", f"Email '{email_id}' not found.", 404))
        return res

    # --- Drafts & Approvals ---
    @router.get("/drafts")
    async def list_drafts() -> Dict[str, Any]:
        d = engine.db.list_drafts()
        return {"drafts": d, "count": len(d)}

    @router.post("/drafts", status_code=201)
    async def create_draft(body: DraftCreateRequest) -> Dict[str, Any]:
        return engine.create_draft(model_to_dict(body))

    @router.post("/drafts/{draft_id}/send")
    async def send_draft(draft_id: str) -> Any:
        try:
            return engine.request_send_draft(draft_id)
        except EmailCalendarError as exc:
            return _err(exc)

    @router.get("/approvals")
    async def list_approvals(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        a = engine.db.list_approvals(status=status)
        return {"approvals": a, "count": len(a)}

    @router.post("/approvals/{approval_id}/decide")
    async def decide_approval(approval_id: str, body: ApprovalDecisionRequest) -> Any:
        try:
            return engine.decide_send_approval(approval_id, body.approved, body.decided_by, body.comment)
        except EmailCalendarError as exc:
            return _err(exc)

    # --- Calendar ---
    @router.get("/calendar/events")
    async def list_events(date: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        ev = engine.db.list_events(date=date)
        return {"events": ev, "count": len(ev)}

    @router.post("/calendar/events", status_code=201)
    async def create_event(body: CalendarEventCreateRequest) -> Any:
        try:
            return engine.create_event(model_to_dict(body))
        except EmailCalendarError as exc:
            return _err(exc)

    @router.patch("/calendar/events/{event_id}/rsvp")
    async def update_rsvp(event_id: str, body: CalendarRsvpRequest) -> Any:
        try:
            return engine.update_rsvp(event_id, body.rsvp_status)
        except EmailCalendarError as exc:
            return _err(exc)

    @router.post("/calendar/find-slots")
    async def find_slots(body: FreeSlotsRequest) -> Any:
        try:
            return engine.find_free_slots(body.date, duration_minutes=body.duration_minutes)
        except EmailCalendarError as exc:
            return _err(exc)

    @router.get("/calendar/export.ics")
    async def export_ics(date: Optional[str] = Query(default=None)) -> PlainTextResponse:
        ics = engine.export_ics(target_date=date)
        return PlainTextResponse(content=ics, media_type="text/calendar")

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
