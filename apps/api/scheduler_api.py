"""
JARVIS OS Automations & Workflows API
Provides task scheduling, cron management, and workflow triggers.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tools.scheduler.task_scheduler import task_scheduler

logger = logging.getLogger("JARVIS.API.Automations")
scheduler_router = APIRouter(prefix="/automations", tags=["automations"])


class TaskCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    schedule: str = Field(..., min_length=1, description="HH:MM (daily), 'every Xs', or 'once'")
    command: str = Field(..., min_length=1)
    args: Optional[List[Any]] = Field(default_factory=list)
    description: Optional[str] = ""


@scheduler_router.get("/tasks")
def list_tasks():
    """Retrieve all scheduled tasks from persistent storage."""
    tasks = task_scheduler.list_tasks()
    return {"status": "ok", "total": len(tasks), "tasks": tasks}


@scheduler_router.post("/tasks")
def create_task(req: TaskCreateRequest):
    """Register a new scheduled task."""
    try:
        task_id = task_scheduler.schedule_task(
            name=req.name,
            schedule=req.schedule,
            command=req.command,
            args=req.args,
            description=req.description or "",
        )
        return {"status": "ok", "task_id": task_id, "name": req.name}
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@scheduler_router.post("/tasks/{task_id}/toggle")
def toggle_task(task_id: int, enable: bool = True):
    """Enable or pause a scheduled task."""
    if enable:
        task_scheduler.resume_task(task_id)
    else:
        task_scheduler.pause_task(task_id)
    return {"status": "ok", "task_id": task_id, "enabled": enable}


@scheduler_router.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """Remove a scheduled task permanently."""
    task_scheduler.delete_task(task_id)
    return {"status": "ok", "task_id": task_id, "deleted": True}


@scheduler_router.post("/tasks/run_due")
def trigger_due():
    """Manually trigger due tasks check."""
    ran = task_scheduler.run_due_tasks()
    return {"status": "ok", "executed": ran}
