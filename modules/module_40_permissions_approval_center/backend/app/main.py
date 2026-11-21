"""FastAPI application entrypoint & host mount helper for JARVIS Module 40 — Permissions & Approval Center."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from modules.module_40_permissions_approval_center.backend.api.routes import build_router
from modules.module_40_permissions_approval_center.backend.app.config import ApprovalConfig
from modules.module_40_permissions_approval_center.backend.services.approval_engine import ApprovalEngine

STATIC_DIR = Path(__file__).resolve().parent / "static"


def mount_module(
    app: FastAPI,
    engine: Optional[ApprovalEngine] = None,
    include_root_ui: bool = False,
) -> ApprovalEngine:
    active_engine = engine or ApprovalEngine()
    app.state.approvals = active_engine
    app.include_router(build_router(active_engine))

    hud_path = STATIC_DIR / "index.html"

    @app.get("/approvals", response_class=HTMLResponse, include_in_schema=False)
    async def approvals_hud() -> HTMLResponse:
        if hud_path.is_file():
            return HTMLResponse(hud_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>JARVIS Module 40 — Permissions &amp; Approval Center HUD</h1>")

    if include_root_ui:
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root_hud() -> HTMLResponse:
            return await approvals_hud()

    return active_engine


def create_app(config: Optional[ApprovalConfig] = None) -> FastAPI:
    cfg = config or ApprovalConfig.from_env()
    app = FastAPI(
        title="JARVIS Module 40 — Permissions & Approval Center",
        version="1.0.0",
        description="Fail-closed policy evaluator, human-in-the-loop approval queue, and immutable governance audit log.",
    )
    origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_module(app, engine=ApprovalEngine(config=cfg), include_root_ui=True)
    return app


app = create_app()
