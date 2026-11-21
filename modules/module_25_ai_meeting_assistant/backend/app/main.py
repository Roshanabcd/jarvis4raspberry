"""FastAPI entrypoint and additive mount hook for JARVIS Module 25."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_25_ai_meeting_assistant.backend.api.routes import build_router
from modules.module_25_ai_meeting_assistant.backend.app.config import MeetingAssistantConfig
from modules.module_25_ai_meeting_assistant.backend.services.meeting_engine import MeetingAssistantEngine

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_app(
    config: Optional[MeetingAssistantConfig] = None,
    engine: Optional[MeetingAssistantEngine] = None,
) -> FastAPI:
    cfg = config or MeetingAssistantConfig.from_env()
    svc = engine or MeetingAssistantEngine(config=cfg)
    app = FastAPI(title="JARVIS OS Module 25 — AI Meeting Assistant", version="1.0.0")
    app.state.meeting_assistant = svc
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_module(app, engine=svc, include_root_ui=True)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        svc.db.close()

    return app


def mount_module(
    app: FastAPI,
    engine: Optional[MeetingAssistantEngine] = None,
    include_root_ui: bool = False,
) -> MeetingAssistantEngine:
    svc = engine or MeetingAssistantEngine()
    app.include_router(build_router(svc))

    def _serve_ui() -> HTMLResponse:
        if STATIC_INDEX.is_file():
            return HTMLResponse(STATIC_INDEX.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 25 — AI Meeting Assistant</h1>")

    app.add_api_route("/meeting-assistant", _serve_ui, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)
    return svc


app = create_app()
