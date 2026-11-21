"""FastAPI application entrypoint & host mount helper for JARVIS Module 41 — Universal Notification Center."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_41_universal_notification_center.backend.api.routes import build_router
from modules.module_41_universal_notification_center.backend.app.config import NotificationConfig
from modules.module_41_universal_notification_center.backend.services.notification_engine import NotificationEngine

STATIC_DIR = Path(__file__).resolve().parent / "static"


def mount_module(
    app: FastAPI,
    engine: Optional[NotificationEngine] = None,
    include_root_ui: bool = False,
) -> NotificationEngine:
    active_engine = engine or NotificationEngine()
    app.state.notifications = active_engine
    app.include_router(build_router(active_engine))

    hud_path = STATIC_DIR / "index.html"

    @app.get("/notifications", response_class=HTMLResponse, include_in_schema=False)
    async def notifications_hud() -> HTMLResponse:
        if hud_path.is_file():
            return HTMLResponse(hud_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 41 — Universal Notification Center HUD</h1>")

    if include_root_ui:
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root_hud() -> HTMLResponse:
            return await notifications_hud()

    return active_engine


def create_app(config: Optional[NotificationConfig] = None) -> FastAPI:
    cfg = config or NotificationConfig.from_env()
    app = FastAPI(
        title="JARVIS Module 41 — Universal Notification Center",
        version="1.0.0",
        description="Local universal notification hub with priority routing, DND critical override, and deduplication.",
    )
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_module(app, engine=NotificationEngine(config=cfg), include_root_ui=True)
    return app


app = create_app()
