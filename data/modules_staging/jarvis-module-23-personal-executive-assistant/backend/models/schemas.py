"""Pydantic schemas for JARVIS Module 23 (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()


class GoalCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=160)
    horizon: str = Field(default="quarterly", description="daily | weekly | quarterly | annual")
    priority: str = Field(default="high", description="critical | high | medium | low")
    target_date: Optional[str] = None
    progress_pct: int = Field(default=0, ge=0, le=100)


class GoalProgressUpdateRequest(BaseModel):
    progress_pct: int = Field(..., ge=0, le=100)
    status: Optional[str] = None


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=180)
    description: str = Field(default="", max_length=1000)
    priority: str = Field(default="p2", description="p1 | p2 | p3 | p4")
    urgent: bool = Field(default=False)
    important: bool = Field(default=True)
    due_date: Optional[str] = None
    estimated_minutes: int = Field(default=45, ge=5, le=480)
    goal_id: Optional[str] = None


class TaskStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="todo | in_progress | done | deferred")


class TimeBlockCreateRequest(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    start_time: str = Field(..., description="HH:MM (24h)")
    end_time: str = Field(..., description="HH:MM (24h)")
    title: str = Field(..., min_length=2, max_length=160)
    block_type: str = Field(default="deep_work", description="deep_work | meeting | admin | break")
    task_id: Optional[str] = None


class PlanDayRequest(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    max_tasks: int = Field(default=4, ge=1, le=12)


class HabitCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    cadence: str = Field(default="daily", description="daily | weekdays")


class HabitCheckinRequest(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")


class FollowUpCreateRequest(BaseModel):
    person: str = Field(..., min_length=1, max_length=100)
    topic: str = Field(..., min_length=2, max_length=200)
    due_date: str = Field(..., description="YYYY-MM-DD")


class FollowUpUpdateRequest(BaseModel):
    status: str = Field(..., description="open | completed | snoozed")
