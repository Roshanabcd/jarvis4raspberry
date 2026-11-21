"""FastAPI REST & WebSocket routes for JARVIS Module 43 — Autonomous Screen Guardian."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_43_autonomous_screen_guardian.backend.adapters.coding_agents import discover_cli_agents
from modules.module_43_autonomous_screen_guardian.backend.models.database import utc_now_iso
from modules.module_43_autonomous_screen_guardian.backend.models.schemas import (
    AnalyzeFrameRequest,
    MonitorStartRequest,
    NotificationActionRequest,
    RepairApprovalRequest,
    RepairCreateRequest,
    SettingsUpdateRequest,
    VoiceCommandRequest,
    model_to_dict,
)
from modules.module_43_autonomous_screen_guardian.backend.services.guardian_service import ScreenGuardianService
from modules.module_43_autonomous_screen_guardian.backend.services.repair_engine import RepairEngineError
from modules.module_43_autonomous_screen_guardian.backend.services.screen_capture import ScreenCaptureError
from modules.module_43_autonomous_screen_guardian.backend.services.system_telemetry import collect_system_telemetry

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(code: str, message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "timestamp": utc_now_iso()}},
    )


def build_router(service: ScreenGuardianService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/screen-guardian", tags=["JARVIS Module 43 — Autonomous Screen Guardian"])

    def require_auth(x_jarvis_token: Optional[str] = Header(default=None)) -> None:
        expected = service.config.api_token
        if expected and x_jarvis_token != expected:
            raise HTTPException(
                status_code=401,
                detail={"code": "UNAUTHORIZED", "message": "Valid X-JARVIS-Token header required."},
            )

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-43-autonomous-screen-guardian",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": service.is_simulated,
            "ocr_available": service.ocr.is_available,
            "timestamp": utc_now_iso(),
        }

    @router.get("/manifest")
    async def manifest() -> Dict[str, Any]:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="manifest.json not found")

    @router.get("/status")
    async def status() -> Dict[str, Any]:
        return service.get_status()

    @router.get("/telemetry")
    async def telemetry() -> Dict[str, Any]:
        return collect_system_telemetry()

    # --- Screen Monitoring ---
    @router.get("/monitors")
    async def list_monitors() -> Dict[str, Any]:
        mons = service.capture.list_monitors()
        return {"monitors": mons, "display_server": service.capture.detect_display_server()}

    @router.post("/monitor/start", dependencies=[Depends(require_auth)])
    async def start_monitor(body: MonitorStartRequest) -> Any:
        try:
            st = service.capture.start(
                explicit_consent=body.explicit_consent,
                monitor_id=body.monitor_id,
                interval_sec=body.interval_sec,
                excluded_windows=body.excluded_windows or None,
                excluded_regions=body.excluded_regions or None,
            )
            service.db.add_log("monitor.started", f"Monitoring started on monitor '{body.monitor_id}'")
            return st
        except ScreenCaptureError as exc:
            return _err(exc.code, exc.message, exc.status_code)

    @router.post("/monitor/pause", dependencies=[Depends(require_auth)])
    async def pause_monitor() -> Dict[str, Any]:
        return service.capture.pause()

    @router.post("/monitor/resume", dependencies=[Depends(require_auth)])
    async def resume_monitor() -> Any:
        try:
            return service.capture.resume()
        except ScreenCaptureError as exc:
            return _err(exc.code, exc.message, exc.status_code)

    @router.post("/monitor/stop", dependencies=[Depends(require_auth)])
    async def stop_monitor() -> Dict[str, Any]:
        st = service.capture.stop()
        service.db.add_log("monitor.stopped", "Monitoring stopped by user")
        return st

    @router.get("/monitor/preview")
    async def monitor_preview() -> Dict[str, Any]:
        if not service.capture.last_frame:
            return {"has_frame": False, "frame": None}
        return {"has_frame": True, "frame": service.capture.last_frame.to_metadata(include_preview_b64=True)}

    # --- Capture, OCR & Error Analysis ---
    @router.post("/analyze", dependencies=[Depends(require_auth)])
    async def analyze_frame(body: AnalyzeFrameRequest) -> Any:
        try:
            return await service.analyze_frame(
                image_base64=body.image_base64,
                ocr_text_override=body.ocr_text_override,
                source_app=body.source_app,
                window_title=body.window_title,
                use_vision_model=body.use_vision_model,
                require_active_session=False,
            )
        except ScreenCaptureError as exc:
            return _err(exc.code, exc.message, exc.status_code)

    @router.get("/ocr/history")
    async def ocr_history(q: Optional[str] = Query(default=None), limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
        items = service.db.list_ocr_history(query=q, limit=limit)
        return {"entries": items, "count": len(items)}

    @router.get("/errors")
    async def list_errors(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        errs = service.db.list_errors(status=status)
        return {"errors": errs, "count": len(errs)}

    @router.get("/notifications")
    async def list_notifications() -> Dict[str, Any]:
        items = service.db.list_notifications()
        return {"notifications": items, "count": len(items)}

    @router.post("/notifications/{notification_id}/action", dependencies=[Depends(require_auth)])
    async def notification_action(notification_id: str, body: NotificationActionRequest) -> Any:
        try:
            return service.handle_notification_action(notification_id, body.action)
        except KeyError as exc:
            return _err("NOTIFICATION_NOT_FOUND", str(exc), 404)
        except ValueError as exc:
            return _err("INVALID_ACTION", str(exc), 422)

    # --- Coding Agents & Auto-Repair ---
    @router.get("/agents")
    async def list_agents() -> Dict[str, Any]:
        agents = discover_cli_agents()
        return {"agents": agents, "count": len(agents)}

    @router.get("/repairs")
    async def list_repairs() -> Dict[str, Any]:
        jobs = service.db.list_repairs()
        return {"repairs": jobs, "count": len(jobs)}

    @router.post("/repairs", status_code=201, dependencies=[Depends(require_auth)])
    async def create_repair(body: RepairCreateRequest) -> Any:
        try:
            return service.repair.create_repair_request(model_to_dict(body))
        except (RepairEngineError, PermissionError) as exc:
            code = exc.code if isinstance(exc, RepairEngineError) else "FORBIDDEN_ARG"
            st = exc.status_code if isinstance(exc, RepairEngineError) else 403
            return _err(code, str(exc), st)

    @router.post("/repairs/{repair_id}/approve", dependencies=[Depends(require_auth)])
    async def approve_repair(repair_id: str, body: RepairApprovalRequest) -> Any:
        try:
            return service.repair.approve_repair(repair_id, body.decision, body.reviewer, body.notes)
        except RepairEngineError as exc:
            return _err(exc.code, exc.message, exc.status_code)

    @router.post("/repairs/{repair_id}/execute", dependencies=[Depends(require_auth)])
    async def execute_repair(repair_id: str) -> Any:
        try:
            return await service.repair.execute_repair(repair_id)
        except RepairEngineError as exc:
            return _err(exc.code, exc.message, exc.status_code)

    @router.post("/repairs/{repair_id}/cancel", dependencies=[Depends(require_auth)])
    async def cancel_repair(repair_id: str) -> Any:
        try:
            return await service.repair.cancel_repair(repair_id)
        except RepairEngineError as exc:
            return _err(exc.code, exc.message, exc.status_code)

    # --- Voice Adapter, Settings & Logs ---
    @router.post("/voice/command", dependencies=[Depends(require_auth)])
    async def voice_command(body: VoiceCommandRequest) -> Dict[str, Any]:
        return service.voice.handle_command(
            utterance=body.utterance,
            speaker_source=body.speaker_source,
            explicit_authorization=body.explicit_authorization,
            target_error_id=body.target_error_id,
            workspace_path=body.workspace_path,
        )

    @router.get("/settings")
    async def get_settings() -> Dict[str, Any]:
        return service.get_settings()

    @router.put("/settings", dependencies=[Depends(require_auth)])
    async def update_settings(body: SettingsUpdateRequest) -> Dict[str, Any]:
        return service.update_settings(model_to_dict(body))

    @router.get("/logs")
    async def list_logs(limit: int = Query(default=100, ge=1, le=500)) -> Dict[str, Any]:
        logs = service.db.list_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}

    @router.websocket("/ws/stream")
    async def ws_stream(websocket: WebSocket) -> None:
        await websocket.accept()
        queue = service.subscribe_ws()
        try:
            await websocket.send_json({"event_type": "ws.connected", "monitoring": service.capture.get_status()})
            while True:
                recv_task = asyncio.create_task(websocket.receive_text())
                evt_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait({recv_task, evt_task}, timeout=10.0, return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
                    try:
                        await p
                    except (asyncio.CancelledError, Exception):
                        pass
                if recv_task in done:
                    _ = recv_task.result()
                elif evt_task in done:
                    await websocket.send_json(evt_task.result())
                else:
                    await websocket.send_json({"event_type": "ws.heartbeat", "monitoring": service.capture.get_status()})
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            service.unsubscribe_ws(queue)

    return router
