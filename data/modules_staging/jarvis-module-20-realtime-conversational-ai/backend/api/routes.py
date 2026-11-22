"""FastAPI REST & streaming WebSocket routes for JARVIS Module 20."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from backend.adapters.provider_adapters import PERSONA_PROFILES
from backend.models.database import utc_now_iso
from backend.models.schemas import (
    ChatMessageRequest,
    ProviderConfigUpdateRequest,
    SessionCreateRequest,
)
from backend.services.conversation_engine import ConversationalEngine

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def build_router(engine: ConversationalEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/conversational-ai", tags=["JARVIS Module 20 — Real-Time Conversational AI"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-20-realtime-conversational-ai",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "provider": engine.config.provider,
            "simulated": engine.get_status()["simulated"],
            "lip_sync_mode": "approximate_syllable_viseme",
            "timestamp": utc_now_iso(),
        }

    @router.get("/manifest")
    async def get_manifest() -> Dict[str, Any]:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="manifest.json not found")

    @router.get("/status")
    async def status() -> Dict[str, Any]:
        return engine.get_status()

    @router.get("/personas")
    async def list_personas() -> Dict[str, Any]:
        return {"personas": list(PERSONA_PROFILES.values())}

    @router.put("/provider")
    async def update_provider(body: ProviderConfigUpdateRequest) -> Dict[str, Any]:
        engine.config.provider = body.provider
        engine.config.provider_url = body.provider_url
        engine.config.provider_model = body.provider_model
        return engine.get_status()

    # --- Sessions & Context ---
    @router.get("/sessions")
    async def list_sessions() -> Dict[str, Any]:
        sessions = engine.db.list_sessions()
        return {"sessions": sessions, "count": len(sessions)}

    @router.post("/sessions", status_code=201)
    async def create_session(body: SessionCreateRequest) -> Dict[str, Any]:
        return engine.create_session(body.title, persona=body.persona.value, system_prompt=body.system_prompt)

    @router.get("/sessions/{session_id}/messages")
    async def list_messages(session_id: str) -> Dict[str, Any]:
        if not engine.db.get_session(session_id):
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
        msgs = engine.db.list_messages(session_id)
        return {"session_id": session_id, "messages": msgs, "count": len(msgs)}

    @router.delete("/sessions/{session_id}/messages")
    async def clear_messages(session_id: str) -> Dict[str, Any]:
        cleared = engine.db.clear_session_messages(session_id)
        return {"session_id": session_id, "cleared": cleared}

    @router.delete("/sessions/{session_id}")
    async def delete_session(session_id: str) -> Dict[str, Any]:
        deleted = engine.db.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
        return {"deleted": True, "session_id": session_id}

    # --- Chat & Barge-In ---
    @router.post("/chat")
    async def chat_turn(body: ChatMessageRequest) -> Dict[str, Any]:
        return await engine.complete_turn(
            session_id=body.session_id,
            user_content=body.content,
            persona=body.persona.value,
            simulate_provider_error=body.simulate_provider_error,
        )

    @router.post("/sessions/{session_id}/interrupt")
    async def interrupt_session(session_id: str) -> Dict[str, Any]:
        return engine.interrupt_session(session_id)

    @router.websocket("/ws/chat")
    async def ws_chat(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json({"event": "ws.connected", "status": engine.get_status()})
        active_task: asyncio.Task[Any] | None = None
        current_sid: str | None = None

        async def _stream_to_ws(sid: str | None, content: str, persona: str, sim_err: bool) -> None:
            nonlocal current_sid
            async for evt in engine.stream_turn(sid, content, persona=persona, simulate_provider_error=sim_err):
                current_sid = evt.get("session_id", current_sid)
                await websocket.send_json(evt)

        try:
            while True:
                raw = await websocket.receive_json()
                msg_type = raw.get("type", "chat")
                if msg_type == "interrupt":
                    target_sid = raw.get("session_id") or current_sid
                    if target_sid:
                        res = engine.interrupt_session(target_sid)
                        await websocket.send_json({"event": "interrupt.ack", **res})
                elif msg_type == "chat":
                    if active_task and not active_task.done() and current_sid:
                        engine.interrupt_session(current_sid)
                    active_task = asyncio.create_task(
                        _stream_to_ws(
                            raw.get("session_id"),
                            str(raw.get("content", "")),
                            str(raw.get("persona", "aria")),
                            bool(raw.get("simulate_provider_error", False)),
                        )
                    )
        except (WebSocketDisconnect, RuntimeError):
            if current_sid:
                engine.interrupt_session(current_sid)
            if active_task and not active_task.done():
                active_task.cancel()

    return router
