"""FastAPI application factory & JARVIS OS mount helper for Module 34."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.api.routes import build_router
from backend.app.config import FinanceConfig
from backend.services.finance_engine import FinanceEngine

STATIC_HTML = Path(__file__).resolve().parent / "static" / "index.html"


def mount_module(
    app: FastAPI,
    engine: Optional[FinanceEngine] = None,
    include_root_ui: bool = False,
) -> FinanceEngine:
    eng = engine or FinanceEngine()
    app.state.finance = eng
    app.include_router(build_router(eng))

    def _serve_ui() -> HTMLResponse:
        if STATIC_HTML.is_file():
            return HTMLResponse(STATIC_HTML.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Personal Finance UI not built.</h1>", status_code=200)

    app.add_api_route("/finance", _serve_ui, methods=["GET"], include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], include_in_schema=False)
    return eng


def create_app(config: Optional[FinanceConfig] = None) -> FastAPI:
    cfg = config or FinanceConfig.from_env()
    app = FastAPI(
        title="JARVIS OS — Module 34: Personal Finance Manager",
        version="1.0.0",
    )
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    engine = FinanceEngine(config=cfg)
    mount_module(app, engine=engine, include_root_ui=True)
    return app


app = create_app()
