"""FastAPI REST & WebSocket routes for JARVIS Module 23 — Personal Executive Assistant."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.models.database import utc_now_iso
from backend.models.schemas import (
    FollowUpCreateRequest,
    FollowUpUpdateRequest,
    GoalCreateRequest,
    GoalProgressUpdateRequest,
    HabitCheckinRequest,
    HabitCreateRequest,
    PlanDayRequest,
    TaskCreateRequest,
    TaskStatusUpdateRequest,
    TimeBlockCreateRequest,
    model_to_dict,
)
from backend.services.executive_engine import ExecutiveAssistantError, PersonalExecutiveEngine

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: ExecutiveAssistantError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: PersonalExecutiveEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/executive-assistant", tags=["JARVIS Module 23 — Personal Executive Assistant"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-23-personal-executive-assistant",
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

    @router.get("/briefing")
    async def briefing(date: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        return engine.generate_briefing(target_date=date)

    # --- Goals ---
    @router.get("/goals")
    async def list_goals() -> Dict[str, Any]:
        g = engine.db.list_goals()
        return {"goals": g, "count": len(g)}

    @router.post("/goals", status_code=201)
    async def create_goal(body: GoalCreateRequest) -> Dict[str, Any]:
        return engine.create_goal(model_to_dict(body))

    @router.patch("/goals/{goal_id}")
    async def update_goal(goal_id: str, body: GoalProgressUpdateRequest) -> Any:
        try:
            return engine.update_goal(goal_id, body.progress_pct, status=body.status)
        except ExecutiveAssistantError as exc:
            return _err(exc)

    # --- Tasks ---
    @router.get("/tasks")
    async def list_tasks(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        t = engine.db.list_tasks(status=status)
        return {"tasks": t, "count": len(t)}

    @router.post("/tasks", status_code=201)
    async def create_task(body: TaskCreateRequest) -> Dict[str, Any]:
        return engine.create_task(model_to_dict(body))

    @router.patch("/tasks/{task_id}")
    async def update_task(task_id: str, body: TaskStatusUpdateRequest) -> Any:
        try:
            return engine.update_task_status(task_id, body.status)
        except ExecutiveAssistantError as exc:
            return _err(exc)

    # --- Time Blocks & Auto-Plan ---
    @router.get("/time-blocks")
    async def list_time_blocks(date: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        b = engine.db.list_time_blocks(date=date)
        return {"time_blocks": b, "count": len(b)}

    @router.post("/time-blocks", status_code=201)
    async def create_time_block(body: TimeBlockCreateRequest) -> Any:
        try:
            return engine.create_time_block(model_to_dict(body))
        except ExecutiveAssistantError as exc:
            return _err(exc)

    @router.post("/plan-day")
    async def plan_day(body: PlanDayRequest) -> Any:
        try:
            return engine.plan_day(body.date, max_tasks=body.max_tasks)
        except ExecutiveAssistantError as exc:
            return _err(exc)

    # --- Habits ---
    @router.get("/habits")
    async def list_habits(date: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        h = engine.list_habits_with_streaks(reference_date=date)
        return {"habits": h, "count": len(h)}

    @router.post("/habits", status_code=201)
    async def create_habit(body: HabitCreateRequest) -> Dict[str, Any]:
        return engine.create_habit(body.name, cadence=body.cadence)

    @router.post("/habits/{habit_id}/checkin")
    async def checkin_habit(habit_id: str, body: HabitCheckinRequest) -> Any:
        try:
            return engine.checkin_habit(habit_id, body.date)
        except ExecutiveAssistantError as exc:
            return _err(exc)

    # --- Follow-ups ---
    @router.get("/followups")
    async def list_followups(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        f = engine.db.list_followups(status=status)
        return {"followups": f, "count": len(f)}

    @router.post("/followups", status_code=201)
    async def create_followup(body: FollowUpCreateRequest) -> Dict[str, Any]:
        return engine.create_followup(model_to_dict(body))

    @router.patch("/followups/{followup_id}")
    async def update_followup(followup_id: str, body: FollowUpUpdateRequest) -> Any:
        try:
            return engine.update_followup(followup_id, body.status)
        except ExecutiveAssistantError as exc:
            return _err(exc)

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
