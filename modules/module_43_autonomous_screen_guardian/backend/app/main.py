"""FastAPI application entrypoint & host mount adapter for JARVIS Module 43."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_43_autonomous_screen_guardian.backend.api.routes import build_router
from modules.module_43_autonomous_screen_guardian.backend.app.config import ScreenGuardianConfig
from modules.module_43_autonomous_screen_guardian.backend.services.guardian_service import ScreenGuardianService

STATIC_DIR = Path(__file__).resolve().parent / "static"


def mount_module(
    app: FastAPI,
    service: Optional[ScreenGuardianService] = None,
    include_root_ui: bool = False,
) -> ScreenGuardianService:
    """Attach Module 43 routes, cleanup hook, and HUD to any host FastAPI app."""
    active = service or ScreenGuardianService()
    app.state.screen_guardian = active
    app.include_router(build_router(active))

    @app.on_event("shutdown")
    async def _shutdown_guardian() -> None:
        active.capture.stop()
        active.db.close()

    hud_path = STATIC_DIR / "index.html"

    @app.api_route("/screen-guardian", methods=["GET", "HEAD"], response_class=HTMLResponse, include_in_schema=False)
    @app.api_route("/screen-guardian/", methods=["GET", "HEAD"], response_class=HTMLResponse, include_in_schema=False)
    async def guardian_hud() -> HTMLResponse:
        if hud_path.is_file():
            return HTMLResponse(hud_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 43 — Autonomous Screen Guardian</h1>")

    if include_root_ui:
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root_hud() -> HTMLResponse:
            return await guardian_hud()

    return active


def create_app(config: Optional[ScreenGuardianConfig] = None) -> FastAPI:
    cfg = config or ScreenGuardianConfig.from_env()
    app = FastAPI(
        title="JARVIS Module 43 — Autonomous Screen Guardian & AI Repair Agent",
        version="1.0.0",
        description="User-authorized desktop screen monitoring, real Tesseract OCR, contextual error detection, and permission-controlled AI code repair.",
    )
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_module(app, service=ScreenGuardianService(config=cfg), include_root_ui=True)
    return app


app = create_app()
