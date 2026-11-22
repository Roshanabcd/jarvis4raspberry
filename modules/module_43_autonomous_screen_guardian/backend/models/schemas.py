"""Pydantic v1/v2 compatible schemas for JARVIS Module 43 — Autonomous Screen Guardian."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


class MonitorStartRequest(BaseModel):
    explicit_consent: bool = Field(..., description="Must be true to start screen monitoring")
    monitor_id: str = Field(default="primary", max_length=64)
    interval_sec: float = Field(default=2.0, ge=0.5, le=60.0)
    excluded_windows: List[str] = Field(default_factory=list)
    excluded_regions: List[Dict[str, int]] = Field(default_factory=list)


class AnalyzeFrameRequest(BaseModel):
    image_base64: Optional[str] = None
    ocr_text_override: Optional[str] = None
    source_app: str = Field(default="Unknown Application", max_length=120)
    window_title: str = Field(default="", max_length=200)
    use_vision_model: bool = Field(default=False)


class NotificationActionRequest(BaseModel):
    action: str = Field(..., description="view | explain | prepare_fix | dismiss | ignore_similar")


class RepairCreateRequest(BaseModel):
    error_id: Optional[str] = None
    workspace_path: str = Field(..., min_length=1, max_length=512)
    agent_id: str = Field(default="reference_local_repair_agent", max_length=80)
    mode: str = Field(default="assisted_repair", description="observe_only | suggest_fix | assisted_repair | trusted_workspace_autopilot")
    summary: str = Field(..., min_length=1, max_length=500)
    error_context: str = Field(default="", max_length=8000)
    test_command: List[str] = Field(default_factory=list)
    target_files: List[str] = Field(default_factory=list)


class RepairApprovalRequest(BaseModel):
    decision: str = Field(..., description="approve | reject")
    reviewer: str = Field(default="operator", min_length=1, max_length=80)
    notes: str = Field(default="", max_length=500)


class SettingsUpdateRequest(BaseModel):
    capture_interval_sec: Optional[float] = Field(default=None, ge=0.5, le=60.0)
    vision_provider: Optional[str] = Field(default=None, max_length=64)
    allow_remote_vision_upload: Optional[bool] = None
    performance_mode: Optional[str] = Field(default=None, max_length=32)
    disabled_alert_categories: Optional[List[str]] = None
    excluded_windows: Optional[List[str]] = None
    trusted_workspaces: Optional[List[str]] = None


class VoiceCommandRequest(BaseModel):
    utterance: str = Field(..., min_length=1, max_length=500)
    speaker_source: str = Field(default="user_mic", description="Must be 'user_mic'; 'screen_media' is ignored")
    explicit_authorization: bool = Field(default=False)
    target_error_id: Optional[str] = None
    workspace_path: Optional[str] = None
