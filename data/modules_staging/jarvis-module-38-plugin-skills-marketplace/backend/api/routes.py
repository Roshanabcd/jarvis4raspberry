"""FastAPI REST & WebSocket routes for JARVIS Module 38 — Plugin & Skills Marketplace."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import PackageInstallRequest, PackagePublishRequest, PackageToggleRequest, model_to_dict
from backend.services.marketplace_engine import MarketplaceEngine, MarketplaceError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: MarketplaceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: MarketplaceEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/marketplace", tags=["JARVIS Module 38 — Plugin & Skills Marketplace"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-38-plugin-skills-marketplace",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.is_simulated,
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

    @router.get("/packages")
    async def list_packages(q: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        pkgs = engine.db.list_packages(query=q)
        return {"packages": pkgs, "count": len(pkgs)}

    @router.post("/packages", status_code=201)
    async def publish_package(body: PackagePublishRequest) -> Any:
        try:
            return engine.publish_package(model_to_dict(body))
        except MarketplaceError as exc:
            return _err(exc)

    @router.post("/packages/{package_id}/install")
    async def install_package(package_id: str, body: PackageInstallRequest) -> Any:
        try:
            return engine.install_package(package_id, expected_sha256=body.expected_sha256, enabled=body.enabled)
        except MarketplaceError as exc:
            return _err(exc)

    @router.post("/packages/{package_id}/toggle")
    async def toggle_package(package_id: str, body: PackageToggleRequest) -> Any:
        try:
            return engine.toggle_package(package_id, enabled=body.enabled)
        except MarketplaceError as exc:
            return _err(exc)

    @router.delete("/packages/{package_id}/install")
    async def uninstall_package(package_id: str) -> Any:
        try:
            return engine.uninstall_package(package_id)
        except MarketplaceError as exc:
            return _err(exc)

    @router.get("/audit")
    async def list_audit() -> Dict[str, Any]:
        events = engine.db.list_audit()
        return {"events": events, "count": len(events)}

    @router.websocket("/ws/registry")
    async def ws_registry(websocket: WebSocket) -> None:
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
