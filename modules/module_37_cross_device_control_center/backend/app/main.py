"""FastAPI application entrypoint & host mount helper for JARVIS Module 37 — Cross-Device Control Center."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_37_cross_device_control_center.backend.api.routes import build_router
from modules.module_37_cross_device_control_center.backend.app.config import DeviceMeshConfig
from modules.module_37_cross_device_control_center.backend.services.device_mesh_engine import DeviceMeshEngine

STATIC_DIR = Path(__file__).resolve().parent / "static"


def mount_module(
    app: FastAPI,
    engine: Optional[DeviceMeshEngine] = None,
    include_root_ui: bool = False,
) -> DeviceMeshEngine:
    active_engine = engine or DeviceMeshEngine()
    app.state.devices = active_engine
    app.include_router(build_router(active_engine))

    hud_path = STATIC_DIR / "index.html"

    @app.get("/devices", response_class=HTMLResponse, include_in_schema=False)
    async def devices_hud() -> HTMLResponse:
        if hud_path.is_file():
            return HTMLResponse(hud_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 37 — Cross-Device Control Center HUD</h1>")

    if include_root_ui:
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root_hud() -> HTMLResponse:
            return await devices_hud()

    return active_engine


def create_app(config: Optional[DeviceMeshConfig] = None) -> FastAPI:
    cfg = config or DeviceMeshConfig.from_env()
    app = FastAPI(
        title="JARVIS Module 37 — Cross-Device Control Center",
        version="1.0.0",
        description="Unified cross-device mesh registry, capability-guarded remote command bridge, and clipboard sync bus.",
    )
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_module(app, engine=DeviceMeshEngine(config=cfg), include_root_ui=True)
    return app


app = create_app()
