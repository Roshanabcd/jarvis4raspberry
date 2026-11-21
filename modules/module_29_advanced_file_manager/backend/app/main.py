"""FastAPI application entrypoint & JARVIS OS host mount hook for Module 29."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_29_advanced_file_manager.backend.api.routes import build_router
from modules.module_29_advanced_file_manager.backend.app.config import FileManagerConfig
from modules.module_29_advanced_file_manager.backend.services.file_engine import FileManagerEngine

STATIC_HTML = Path(__file__).resolve().parent / "static" / "index.html"


def mount_module(
    app: FastAPI,
    engine: Optional[FileManagerEngine] = None,
    include_root_ui: bool = False,
) -> FileManagerEngine:
    eng = engine or FileManagerEngine()
    app.state.file_manager = eng
    app.include_router(build_router(eng))

    async def _serve_ui() -> HTMLResponse:
        if STATIC_HTML.is_file():
            return HTMLResponse(content=STATIC_HTML.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 29 — Advanced File Manager UI missing</h1>", status_code=404)

    app.add_api_route("/file-manager", _serve_ui, methods=["GET"], include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], include_in_schema=False)
    return eng


def create_app(
    config: Optional[FileManagerConfig] = None,
    engine: Optional[FileManagerEngine] = None,
) -> FastAPI:
    cfg = config or FileManagerConfig.from_env()
    eng = engine or FileManagerEngine(config=cfg)
    app = FastAPI(title="JARVIS OS — Module 29: Advanced File Manager", version="1.0.0")
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_module(app, engine=eng, include_root_ui=True)
    return app


app = create_app()
