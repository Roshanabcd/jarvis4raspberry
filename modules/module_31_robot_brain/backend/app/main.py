"""FastAPI application factory & JARVIS OS mount helper for Module 31."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_31_robot_brain.backend.api.routes import build_router
from modules.module_31_robot_brain.backend.app.config import RobotBrainConfig
from modules.module_31_robot_brain.backend.services.robot_brain_engine import RobotBrainEngine

STATIC_HTML = Path(__file__).resolve().parent / "static" / "index.html"


def mount_module(
    app: FastAPI,
    engine: Optional[RobotBrainEngine] = None,
    include_root_ui: bool = False,
) -> RobotBrainEngine:
    eng = engine or RobotBrainEngine()
    app.state.robot_brain = eng
    app.include_router(build_router(eng))

    def _serve_ui() -> HTMLResponse:
        if STATIC_HTML.is_file():
            return HTMLResponse(STATIC_HTML.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Robot Brain UI not built.</h1>", status_code=200)

    app.add_api_route("/robot-brain", _serve_ui, methods=["GET"], include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], include_in_schema=False)
    return eng


def create_app(config: Optional[RobotBrainConfig] = None) -> FastAPI:
    cfg = config or RobotBrainConfig.from_env()
    app = FastAPI(
        title="JARVIS OS — Module 31: JARVIS Robot Brain",
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
    engine = RobotBrainEngine(config=cfg)
    mount_module(app, engine=engine, include_root_ui=True)
    return app


app = create_app()
