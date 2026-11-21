"""FastAPI application entrypoint & host mount adapter for JARVIS Module 42."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_42_unified_extension_manager.backend.api.routes import build_router
from modules.module_42_unified_extension_manager.backend.app.config import ExtensionManagerConfig
from modules.module_42_unified_extension_manager.backend.services.extension_manager import ExtensionManager

STATIC_DIR = Path(__file__).resolve().parent / "static"


def mount_module(
    app: FastAPI,
    manager: Optional[ExtensionManager] = None,
    include_root_ui: bool = False,
) -> ExtensionManager:
    """Attach Module 42 routes, lifecycle cleanup, and HUD to any host FastAPI app."""
    active = manager or ExtensionManager()
    app.state.extension_manager = active
    app.include_router(build_router(active))

    @app.on_event("shutdown")
    async def _shutdown_manager() -> None:
        active.db.close()

    hud_path = STATIC_DIR / "index.html"

    @app.get("/extensions", response_class=HTMLResponse, include_in_schema=False)
    async def extensions_hud() -> HTMLResponse:
        if hud_path.is_file():
            return HTMLResponse(hud_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 42 — Unified Extension Manager</h1>")

    if include_root_ui:
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root_hud() -> HTMLResponse:
            return await extensions_hud()

    return active


def create_app(config: Optional[ExtensionManagerConfig] = None) -> FastAPI:
    cfg = config or ExtensionManagerConfig.from_env()
    app = FastAPI(
        title="JARVIS Module 42 — Unified Extension Manager & SDK",
        version="1.0.0",
        description="Safe archive scanner, compatibility analyzer, SQLite registry, dry-run install planner, health monitor, and shared SDK.",
    )
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_module(app, manager=ExtensionManager(config=cfg), include_root_ui=True)
    return app


app = create_app()
