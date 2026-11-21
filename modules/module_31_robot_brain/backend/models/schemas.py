"""Pydantic v1/v2 compatible schemas for JARVIS Module 31 — JARVIS Robot Brain."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class MotionCommandRequest(BaseModel):
    linear_mps: float = Field(..., ge=-5.0, le=5.0)
    angular_rps: float = Field(default=0.0, ge=-5.0, le=5.0)
    duration_s: float = Field(default=1.0, gt=0.0, le=30.0)


class SensorReadingRequest(BaseModel):
    front_obstacle_m: Optional[float] = Field(default=None, ge=0.0, le=50.0)
    battery_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    cpu_temp_c: Optional[float] = Field(default=None, ge=0.0, le=120.0)


class EstopRequest(BaseModel):
    reason: str = Field(default="Operator emergency stop", min_length=2, max_length=200)


class EstopResetRequest(BaseModel):
    confirm_reset: bool = Field(default=False)
    operator_note: str = Field(default="", max_length=200)


class WaypointCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    zone: str = Field(default="Main Floor", min_length=2, max_length=80)
    x: float = Field(..., ge=-1000.0, le=1000.0)
    y: float = Field(..., ge=-1000.0, le=1000.0)


class MissionStepItem(BaseModel):
    action: Literal["navigate_to_waypoint", "inspect_zone", "return_to_dock"]
    waypoint_id: Optional[str] = None
    note: str = Field(default="", max_length=200)


class MissionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    steps: List[MissionStepItem] = Field(..., min_items=1)
