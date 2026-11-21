"""FastAPI application entrypoint and JARVIS OS additive mount hook for Module 19."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_19_autonomous_computer_assistant.backend.api.routes import build_router
from modules.module_19_autonomous_computer_assistant.backend.app.config import ComputerAssistantConfig
from modules.module_19_autonomous_computer_assistant.backend.services.assistant_engine import ComputerAssistantEngine

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_app(
    config: Optional[ComputerAssistantConfig] = None,
    engine: Optional[ComputerAssistantEngine] = None,
) -> FastAPI:
    cfg = config or ComputerAssistantConfig.from_env()
    svc = engine or ComputerAssistantEngine(config=cfg)

    app = FastAPI(
        title="JARVIS OS Module 19 — Autonomous Computer Assistant",
        version="1.0.0",
        description="Permission-controlled desktop automation with SafeDemoDesktopAdapter, approvals, E-STOP, dry-run, and replay.",
    )
    app.state.computer_assistant = svc

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
    engine: Optional[ComputerAssistantEngine] = None,
    include_root_ui: bool = False,
) -> ComputerAssistantEngine:
    svc = engine or ComputerAssistantEngine()
    app.include_router(build_router(svc))

    def _serve_ui() -> HTMLResponse:
        if STATIC_INDEX.is_file():
            return HTMLResponse(STATIC_INDEX.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 19 — Autonomous Computer Assistant</h1>")

    app.add_api_route("/computer-assistant", _serve_ui, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)
    if include_root_ui:
        app.add_api_route("/", _serve_ui, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)

    return svc


app = create_app()
