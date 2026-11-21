"""Pydantic v1/v2 compatible schemas for JARVIS Module 37 — Cross-Device Control Center."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[attr-defined]
    return obj.dict()


class DeviceRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    device_type: str = Field(default="laptop", min_length=1, max_length=40)
    platform: str = Field(default="linux", min_length=1, max_length=40)
    capabilities: List[str] = Field(default_factory=lambda: ["clipboard", "media", "notifications"])
    battery_pct: int = Field(default=100, ge=0, le=100)
    online: bool = Field(default=True)


class DeviceHeartbeatRequest(BaseModel):
    online: bool = Field(default=True)
    battery_pct: Optional[int] = Field(default=None, ge=0, le=100)


class DeviceCommandRequest(BaseModel):
    capability: str = Field(..., min_length=1, max_length=40)
    action: str = Field(..., min_length=1, max_length=80)
    params: Dict[str, Any] = Field(default_factory=dict)


class ClipboardSyncRequest(BaseModel):
    source_device_id: str = Field(..., min_length=1, max_length=64)
    content: str = Field(..., min_length=1, max_length=16000)
    mime_type: str = Field(default="text/plain", min_length=1, max_length=64)
