"""Pydantic v1/v2 compatible schemas for JARVIS Module 41 — Universal Notification Center."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[attr-defined]
    return obj.dict()


class NotificationCreateRequest(BaseModel):
    source_module: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=160)
    message: str = Field(..., min_length=1, max_length=2000)
    priority: str = Field(default="normal", min_length=1, max_length=20)
    channels: List[str] = Field(default_factory=lambda: ["hud"])
    dedupe_key: Optional[str] = Field(default=None, max_length=128)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PreferencesUpdateRequest(BaseModel):
    dnd_enabled: bool = Field(default=False)
    allow_critical_during_dnd: bool = Field(default=True)
    enabled_channels: List[str] = Field(default_factory=lambda: ["hud", "desktop", "voice"])
