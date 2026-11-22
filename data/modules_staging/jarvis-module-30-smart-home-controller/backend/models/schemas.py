"""Pydantic v1/v2 compatible schemas for JARVIS Module 30 — Smart Home Controller."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class DeviceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    room: str = Field(..., min_length=2, max_length=80)
    device_type: Literal["light", "thermostat", "smart_plug", "lock", "sensor"]
    rated_watts: float = Field(default=12.0, ge=0.0, le=5000.0)
    initial_state: Dict[str, Any] = Field(default_factory=dict)


class DeviceCommandRequest(BaseModel):
    command: Literal["turn_on", "turn_off", "set_brightness", "set_temp", "lock", "unlock", "update_reading"]
    value: Optional[Any] = Field(default=None)
    confirm_unlock: bool = Field(default=False)


class SceneActionItem(BaseModel):
    device_id: str
    command: Literal["turn_on", "turn_off", "set_brightness", "set_temp", "lock"]
    value: Optional[Any] = None


class SceneCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(default="", max_length=300)
    actions: List[SceneActionItem] = Field(..., min_items=1)


class RuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    sensor_device_id: str
    metric_key: str = Field(default="temp_c", min_length=1, max_length=40)
    operator: Literal[">", ">=", "<", "<=", "=="] = Field(default=">")
    threshold: float
    target_device_id: str
    target_command: Literal["turn_on", "turn_off", "set_brightness", "set_temp", "lock"]
    target_value: Optional[Any] = None
