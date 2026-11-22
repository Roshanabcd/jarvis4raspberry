"""FastAPI entrypoint and additive mount hook for JARVIS Module 22."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_22_intelligent_model_router.backend.api.routes import build_router
from modules.module_22_intelligent_model_router.backend.app.config import ModelRouterConfig
from modules.module_22_intelligent_model_router.backend.services.router_engine import IntelligentModelRouterEngine

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_app(
    config: Optional[ModelRouterConfig] = None,
    engine: Optional[IntelligentModelRouterEngine] = None,
) -> FastAPI:
    cfg = config or ModelRouterConfig.from_env()
    svc = engine or IntelligentModelRouterEngine(config=cfg)
    app = FastAPI(title="JARVIS OS Module 22 — Intelligent AI Model Router", version="1.0.0")
    app.state.model_router = svc
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
    engine: Optional[IntelligentModelRouterEngine] = None,
    include_root_ui: bool = False,
) -> IntelligentModelRouterEngine:
    svc = engine or IntelligentModelRouterEngine()
    app.include_router(build_router(svc))

    def _serve_ui() -> HTMLResponse:
        if STATIC_INDEX.is_file():
            return HTMLResponse(STATIC_INDEX.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 22 — Intelligent AI Model Router</h1>")

    app.add_api_route("/model-router", _serve_ui, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)
    return svc


app = create_app()
