"""FastAPI application entrypoint & host mount helper for JARVIS Module 36 — Screen Vision Assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.api.routes import build_router
from backend.app.config import VisionConfig
from backend.services.vision_engine import VisionEngine

STATIC_DIR = Path(__file__).resolve().parent / "static"


def mount_module(
    app: FastAPI,
    engine: Optional[VisionEngine] = None,
    include_root_ui: bool = False,
) -> VisionEngine:
    active_engine = engine or VisionEngine()
    app.state.vision = active_engine
    app.include_router(build_router(active_engine))

    hud_path = STATIC_DIR / "index.html"

    @app.get("/vision", response_class=HTMLResponse, include_in_schema=False)
    async def vision_hud() -> HTMLResponse:
        if hud_path.is_file():
            return HTMLResponse(hud_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 36 — Screen Vision Assistant HUD</h1>")

    if include_root_ui:
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root_hud() -> HTMLResponse:
            return await vision_hud()

    return active_engine


def create_app(config: Optional[VisionConfig] = None) -> FastAPI:
    cfg = config or VisionConfig.from_env()
    app = FastAPI(
        title="JARVIS Module 36 — Screen Vision Assistant",
        version="1.0.0",
        description="Local screen capture inspector, UI bounding-box analyzer, and grounded screen Q&A assistant.",
    )
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_module(app, engine=VisionEngine(config=cfg), include_root_ui=True)
    return app


app = create_app()
