"""FastAPI application entrypoint & JARVIS OS host mount hook for Module 28."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.api.routes import build_router
from backend.app.config import DataAnalystConfig
from backend.services.analyst_engine import DataAnalystEngine

STATIC_HTML = Path(__file__).resolve().parent / "static" / "index.html"


def mount_module(
    app: FastAPI,
    engine: Optional[DataAnalystEngine] = None,
    include_root_ui: bool = False,
) -> DataAnalystEngine:
    eng = engine or DataAnalystEngine()
    app.state.ai_data_analyst = eng
    app.include_router(build_router(eng))

    async def _serve_ui() -> HTMLResponse:
        if STATIC_HTML.is_file():
            return HTMLResponse(content=STATIC_HTML.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 28 — AI Data Analyst UI missing</h1>", status_code=404)

    app.add_api_route("/ai-data-analyst", _serve_ui, methods=["GET"], include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], include_in_schema=False)
    return eng


def create_app(
    config: Optional[DataAnalystConfig] = None,
    engine: Optional[DataAnalystEngine] = None,
) -> FastAPI:
    cfg = config or DataAnalystConfig.from_env()
    eng = engine or DataAnalystEngine(config=cfg)
    app = FastAPI(title="JARVIS OS — Module 28: AI Data Analyst", version="1.0.0")
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
