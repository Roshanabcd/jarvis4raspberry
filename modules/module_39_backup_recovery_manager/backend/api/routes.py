"""FastAPI REST & WebSocket routes for JARVIS Module 39 — Backup & Recovery Manager."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_39_backup_recovery_manager.backend.models.database import utc_now_iso
from modules.module_39_backup_recovery_manager.backend.models.schemas import SnapshotCreateRequest, SnapshotRestoreRequest
from modules.module_39_backup_recovery_manager.backend.services.backup_engine import BackupEngine, BackupError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: BackupError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: BackupEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/backups", tags=["JARVIS Module 39 — Backup & Recovery Manager"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-39-backup-recovery-manager",
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

    @router.get("/snapshots")
    async def list_snapshots() -> Dict[str, Any]:
        snaps = engine.db.list_snapshots()
        return {"snapshots": snaps, "count": len(snaps)}

    @router.post("/snapshots", status_code=201)
    async def create_snapshot(body: SnapshotCreateRequest) -> Any:
        try:
            return engine.create_snapshot(name=body.name, source_rel_path=body.source_rel_path, notes=body.notes)
        except BackupError as exc:
            return _err(exc)

    @router.post("/snapshots/{snapshot_id}/verify")
    async def verify_snapshot(snapshot_id: str) -> Any:
        try:
            return engine.verify_snapshot(snapshot_id)
        except BackupError as exc:
            return _err(exc)

    @router.post("/snapshots/{snapshot_id}/restore", status_code=201)
    async def restore_snapshot(snapshot_id: str, body: SnapshotRestoreRequest) -> Any:
        try:
            return engine.restore_snapshot(snapshot_id, target_rel_path=body.target_rel_path)
        except BackupError as exc:
            return _err(exc)

    @router.get("/restores")
    async def list_restores(snapshot_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        runs = engine.db.list_restores(snapshot_id=snapshot_id)
        return {"restores": runs, "count": len(runs)}

    @router.websocket("/ws/snapshots")
    async def ws_snapshots(websocket: WebSocket) -> None:
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
