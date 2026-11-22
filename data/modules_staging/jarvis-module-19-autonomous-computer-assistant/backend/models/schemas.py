"""Pydantic schemas for JARVIS Module 19 (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj.dict()


class ActionType(str, Enum):
    DISCOVER_APPS = "discover_apps"
    CAPTURE_SCREENSHOT = "capture_screenshot"
    SELECT_WINDOW = "select_window"
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    KEYBOARD_TYPE = "keyboard_type"
    KEYBOARD_HOTKEY = "keyboard_hotkey"
    LAUNCH_APP = "launch_app"
    FILE_LIST = "file_list"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"


class ActionStatus(str, Enum):
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTED = "executed"
    DRY_RUN = "dry_run"
    REJECTED = "rejected"
    BLOCKED_ESTOP = "blocked_estop"
    FAILED = "failed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionExecuteRequest(BaseModel):
    action_type: ActionType
    params: Dict[str, Any] = Field(default_factory=dict)
    dry_run: Optional[bool] = Field(default=None, description="Overrides global dry_run_default when set")
    requested_by: str = Field(default="operator", min_length=1, max_length=80)
    reason: str = Field(default="", max_length=300)


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    decided_by: str = Field(default="operator", min_length=1, max_length=80)
    comment: str = Field(default="", max_length=500)


class EstopRequest(BaseModel):
    reason: str = Field(default="Operator engaged Emergency Stop", max_length=300)
    triggered_by: str = Field(default="operator", min_length=1, max_length=80)


class DryRunToggleRequest(BaseModel):
    enabled: bool


class PermissionPolicyUpdateRequest(BaseModel):
    allow_screenshot: Optional[bool] = None
    allow_keyboard_mouse: Optional[bool] = None
    allow_app_launch: Optional[bool] = None
    allow_file_write: Optional[bool] = None
    require_approval_for_high_risk: Optional[bool] = None


class ReplayRequest(BaseModel):
    action_ids: List[str] = Field(..., min_items=1, max_items=50)
    dry_run: bool = Field(default=True, description="Replay defaults to dry-run for safety")
    requested_by: str = Field(default="operator", min_length=1, max_length=80)
