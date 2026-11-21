"""FastAPI entrypoint and additive mount hook for JARVIS Module 24."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_24_email_calendar_assistant.backend.api.routes import build_router
from modules.module_24_email_calendar_assistant.backend.app.config import EmailCalendarConfig
from modules.module_24_email_calendar_assistant.backend.services.email_calendar_engine import EmailCalendarEngine

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_app(
    config: Optional[EmailCalendarConfig] = None,
    engine: Optional[EmailCalendarEngine] = None,
) -> FastAPI:
    cfg = config or EmailCalendarConfig.from_env()
    svc = engine or EmailCalendarEngine(config=cfg)
    app = FastAPI(title="JARVIS OS Module 24 — Email & Calendar Assistant", version="1.0.0")
    app.state.email_calendar = svc
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
    engine: Optional[EmailCalendarEngine] = None,
    include_root_ui: bool = False,
) -> EmailCalendarEngine:
    svc = engine or EmailCalendarEngine()
    app.include_router(build_router(svc))

    def _serve_ui() -> HTMLResponse:
        if STATIC_INDEX.is_file():
            return HTMLResponse(STATIC_INDEX.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 24 — Email &amp; Calendar Assistant</h1>")

    app.add_api_route("/email-calendar", _serve_ui, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)
    return svc


app = create_app()
