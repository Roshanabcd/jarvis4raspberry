"""FastAPI APIRouter and WebSocket endpoint for JARVIS Real-Time Speech Translation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .config import SpeechTranslationConfig
from .engine import SpeechTranslationEngine
from .models import (
    CreateSessionRequest,
    GlossaryEntryRecord,
    GlossaryEntryRequest,
    GlossaryListResponse,
    HealthResponse,
    SessionDetailResponse,
    TranslateRequest,
    TranslateResponse,
)

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[SpeechTranslationConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = SpeechTranslationEngine(config=config)
    router = APIRouter(tags=["JARVIS Speech Translation"])

    @router.get("/speech-translation", response_class=HTMLResponse, include_in_schema=False)
    def speech_translation_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Speech Translation UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/speech-translation/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/speech-translation/sessions", response_model=SessionDetailResponse)
    def create_session(req: CreateSessionRequest) -> SessionDetailResponse:
        try:
            return engine.create_session(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/speech-translation/sessions/{session_id}", response_model=SessionDetailResponse)
    def get_session(session_id: str) -> SessionDetailResponse:
        try:
            return engine.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/api/speech-translation/translate", response_model=TranslateResponse)
    def translate(req: TranslateRequest) -> TranslateResponse:
        try:
            return engine.translate(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/api/speech-translation/glossary", response_model=GlossaryEntryRecord)
    def upsert_glossary(req: GlossaryEntryRequest) -> GlossaryEntryRecord:
        return engine.upsert_glossary(req)

    @router.get("/api/speech-translation/glossary", response_model=GlossaryListResponse)
    def list_glossary() -> GlossaryListResponse:
        return engine.list_glossary()

    @router.websocket("/api/speech-translation/ws/{session_id}")
    async def ws_translate(websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        try:
            sess = engine.get_session(session_id)
        except KeyError:
            await websocket.send_json({"error": f"Session '{session_id}' not found."})
            await websocket.close(code=1008)
            return

        await websocket.send_json(
            {
                "event": "connected",
                "session_id": sess.session_id,
                "lang_a": sess.lang_a,
                "lang_b": sess.lang_b,
            }
        )
        try:
            while True:
                payload = await websocket.receive_json()
                text = str(payload.get("text", "")).strip()
                if not text:
                    continue
                src = str(payload.get("source_lang", "auto"))
                tgt = str(payload.get("target_lang", sess.lang_b))
                speaker = str(payload.get("speaker", "speaker_a"))
                use_llm = bool(payload.get("use_llm", False))
                try:
                    res = engine.translate(
                        TranslateRequest(
                            text=text,
                            source_lang=src,
                            target_lang=tgt,
                            session_id=sess.session_id,
                            speaker=speaker,
                            use_llm=use_llm,
                        )
                    )
                    await websocket.send_json(res.dict())
                except Exception as exc:
                    await websocket.send_json({"error": str(exc)})
        except WebSocketDisconnect:
            return

    return router
