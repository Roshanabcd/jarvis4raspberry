"""FastAPI REST & WebSocket routes for JARVIS Module 27 — GitHub & CI/CD Manager."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_27_github_cicd_manager.backend.models.database import utc_now_iso
from modules.module_27_github_cicd_manager.backend.models.schemas import (
    MergePRRequest,
    PRCreateRequest,
    PipelineTriggerRequest,
    ReleaseCreateRequest,
    RepoCreateRequest,
    model_to_dict,
)
from modules.module_27_github_cicd_manager.backend.services.cicd_engine import GitHubCICDEngine, GitHubCICDError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: GitHubCICDError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: GitHubCICDEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/github-cicd", tags=["JARVIS Module 27 — GitHub & CI/CD Manager"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-27-github-cicd-manager",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.adapter.is_simulated,
            "timestamp": utc_now_iso(),
        }

    @router.get("/manifest")
    async def manifest() -> Dict[str, Any]:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="manifest.json not found")

    @router.get("/status")
    async def status() -> Dict[str, Any]:
        return engine.get_status()

    @router.get("/repos")
    async def list_repos() -> Dict[str, Any]:
        repos = engine.db.list_repos()
        return {"repositories": repos, "count": len(repos)}

    @router.post("/repos", status_code=201)
    async def register_repo(body: RepoCreateRequest) -> Any:
        try:
            return engine.register_repo(model_to_dict(body))
        except GitHubCICDError as exc:
            return _err(exc)

    @router.get("/pull-requests")
    async def list_prs(repo_id: Optional[str] = Query(default=None), status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        prs = engine.db.list_prs(repo_id=repo_id, status=status)
        return {"pull_requests": prs, "count": len(prs)}

    @router.post("/pull-requests", status_code=201)
    async def create_pr(body: PRCreateRequest) -> Any:
        try:
            return engine.create_pr(model_to_dict(body))
        except GitHubCICDError as exc:
            return _err(exc)

    @router.post("/pull-requests/{pr_id}/merge")
    async def merge_pr(pr_id: str, body: MergePRRequest) -> Any:
        try:
            return engine.merge_pr(pr_id, strategy=body.strategy, merged_by=body.merged_by)
        except GitHubCICDError as exc:
            return _err(exc)

    @router.get("/pipelines")
    async def list_runs(repo_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        runs = engine.db.list_runs(repo_id=repo_id)
        return {"runs": runs, "count": len(runs)}

    @router.post("/pipelines/trigger", status_code=201)
    async def trigger_pipeline(body: PipelineTriggerRequest) -> Any:
        try:
            return engine.trigger_pipeline(model_to_dict(body))
        except GitHubCICDError as exc:
            return _err(exc)

    @router.get("/releases")
    async def list_releases(repo_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        rels = engine.db.list_releases(repo_id=repo_id)
        return {"releases": rels, "count": len(rels)}

    @router.post("/releases", status_code=201)
    async def create_release(body: ReleaseCreateRequest) -> Any:
        try:
            return engine.create_release(model_to_dict(body))
        except GitHubCICDError as exc:
            return _err(exc)

    @router.post("/releases/{release_id}/rollback")
    async def rollback_release(release_id: str) -> Any:
        try:
            return engine.rollback_release(release_id)
        except GitHubCICDError as exc:
            return _err(exc)

    @router.post("/webhooks/github")
    async def github_webhook(
        request: Request,
        x_hub_signature_256: Optional[str] = Header(default=None),
        x_github_event: str = Header(default="ping"),
    ) -> Any:
        raw = await request.body()
        if not engine.verify_webhook_signature(raw, x_hub_signature_256):
            return _err(GitHubCICDError("INVALID_SIGNATURE", "Invalid or missing X-Hub-Signature-256.", 401))
        return {"accepted": True, "event": x_github_event, "bytes": len(raw), "timestamp": utc_now_iso()}

    @router.websocket("/ws/events")
    async def ws_events(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            await websocket.send_json({"event_type": "ws.connected", "status": engine.get_status()})
            while True:
                recv = asyncio.create_task(websocket.receive_text())
                done, _ = await asyncio.wait({recv}, timeout=10.0)
                if recv in done:
                    _ = recv.result()
                else:
                    recv.cancel()
                    try:
                        await recv
                    except (asyncio.CancelledError, Exception):
                        pass
                    await websocket.send_json({"event_type": "ws.heartbeat", "status": engine.get_status()})
        except (WebSocketDisconnect, RuntimeError):
            pass

    return router
