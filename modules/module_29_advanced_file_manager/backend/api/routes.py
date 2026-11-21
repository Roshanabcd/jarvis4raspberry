"""FastAPI REST & WebSocket routes for JARVIS Module 29 — Advanced File Manager."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_29_advanced_file_manager.backend.models.database import utc_now_iso
from modules.module_29_advanced_file_manager.backend.models.schemas import DirCreateRequest, FileWriteRequest, MoveRequest, OrganizeRequest, TagRequest
from modules.module_29_advanced_file_manager.backend.services.file_engine import FileManagerEngine, FileManagerError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: FileManagerError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: FileManagerEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/file-manager", tags=["JARVIS Module 29 — Advanced File Manager"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-29-advanced-file-manager",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.classifier.is_simulated,
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

    @router.get("/files")
    async def list_files(dir: str = Query(default="")) -> Any:
        try:
            return engine.list_files(dir)
        except FileManagerError as exc:
            return _err(exc)

    @router.post("/files", status_code=201)
    async def write_file(body: FileWriteRequest) -> Any:
        try:
            return engine.write_file(body.rel_path, body.content)
        except FileManagerError as exc:
            return _err(exc)

    @router.get("/files/read")
    async def read_file(path: str = Query(..., min_length=1)) -> Any:
        try:
            return engine.read_file(path)
        except FileManagerError as exc:
            return _err(exc)

    @router.post("/dirs", status_code=201)
    async def create_dir(body: DirCreateRequest) -> Any:
        try:
            return engine.create_dir(body.rel_path)
        except FileManagerError as exc:
            return _err(exc)

    @router.post("/files/move")
    async def move_file(body: MoveRequest) -> Any:
        try:
            return engine.move_path(body.src_path, body.dst_path)
        except FileManagerError as exc:
            return _err(exc)

    @router.delete("/files")
    async def delete_file(path: str = Query(..., min_length=1)) -> Any:
        try:
            return engine.soft_delete(path)
        except FileManagerError as exc:
            return _err(exc)

    @router.get("/trash")
    async def list_trash() -> Dict[str, Any]:
        items = engine.db.list_trash()
        return {"trash": items, "count": len(items)}

    @router.post("/trash/{trash_id}/restore")
    async def restore_trash(trash_id: str) -> Any:
        try:
            return engine.restore_trash(trash_id)
        except FileManagerError as exc:
            return _err(exc)

    @router.post("/tags")
    async def set_tags(body: TagRequest) -> Any:
        try:
            _ = engine._resolve_safe(body.rel_path)
            return engine.db.set_tags(body.rel_path.strip().lstrip("/"), body.tags)
        except FileManagerError as exc:
            return _err(exc)

    @router.get("/duplicates")
    async def find_duplicates() -> Dict[str, Any]:
        return engine.find_duplicates()

    @router.post("/organize")
    async def organize_root(body: OrganizeRequest) -> Dict[str, Any]:
        return engine.organize_root(dry_run=body.dry_run)

    @router.get("/search")
    async def search(q: str = Query(..., min_length=1)) -> Dict[str, Any]:
        return engine.search_files(q)

    @router.get("/audit")
    async def audit() -> Dict[str, Any]:
        logs = engine.db.list_audits()
        return {"logs": logs, "count": len(logs)}

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
