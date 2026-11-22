"""FastAPI application factory & JARVIS OS mount helper for Module 33."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_33_defensive_cybersecurity_agent.backend.api.routes import build_router
from modules.module_33_defensive_cybersecurity_agent.backend.app.config import CyberSecurityConfig
from modules.module_33_defensive_cybersecurity_agent.backend.services.security_engine import DefensiveSecurityEngine

STATIC_HTML = Path(__file__).resolve().parent / "static" / "index.html"


def mount_module(
    app: FastAPI,
    engine: Optional[DefensiveSecurityEngine] = None,
    include_root_ui: bool = False,
) -> DefensiveSecurityEngine:
    eng = engine or DefensiveSecurityEngine()
    app.state.cybersecurity = eng
    app.include_router(build_router(eng))

    def _serve_ui() -> HTMLResponse:
        if STATIC_HTML.is_file():
            return HTMLResponse(STATIC_HTML.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Defensive Cybersecurity UI not built.</h1>", status_code=200)

    app.add_api_route("/cybersecurity", _serve_ui, methods=["GET"], include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], include_in_schema=False)
    return eng


def create_app(config: Optional[CyberSecurityConfig] = None) -> FastAPI:
    cfg = config or CyberSecurityConfig.from_env()
    app = FastAPI(
        title="JARVIS OS — Module 33: Defensive Cybersecurity Agent",
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
    engine = DefensiveSecurityEngine(config=cfg)
    mount_module(app, engine=engine, include_root_ui=True)
    return app


app = create_app()
