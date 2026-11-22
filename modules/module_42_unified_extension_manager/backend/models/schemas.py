"""Pydantic v1/v2 compatible schemas for JARVIS Module 42."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


class ScanFolderRequest(BaseModel):
    folder_path: str = Field(..., min_length=1, max_length=512)
    register_discovered: bool = Field(default=True)
    target_arch: str = Field(default="arm64", max_length=32)


class ModuleRegisterRequest(BaseModel):
    module_id: str = Field(..., min_length=1, max_length=120)
    name: str = Field(..., min_length=1, max_length=160)
    version: str = Field(default="1.0.0", max_length=40)
    category: str = Field(default="extension", max_length=80)
    source_archive: Optional[str] = None
    installed_location: Optional[str] = None
    integration_status: str = Field(default="discovered", max_length=40)
    enabled: bool = Field(default=False)
    health_endpoint: Optional[str] = None
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    required_permissions: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class ModuleToggleRequest(BaseModel):
    enabled: bool


class ModuleConfigUpdateRequest(BaseModel):
    config: Dict[str, Any] = Field(default_factory=dict)
    health_endpoint: Optional[str] = None
    installed_location: Optional[str] = None


class InstallPlanRequest(BaseModel):
    module_ids: List[str] = Field(default_factory=list)
    target_arch: str = Field(default="arm64", max_length=32)


class ApprovalCreateRequest(BaseModel):
    module_id: str = Field(..., min_length=1, max_length=120)
    action: str = Field(..., min_length=1, max_length=80)
    summary: str = Field(..., min_length=1, max_length=500)
    requested_by: str = Field(default="operator", max_length=80)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="'approve' or 'reject'")
    reviewer: str = Field(default="operator", min_length=1, max_length=80)
    notes: str = Field(default="", max_length=500)


class EventPublishRequest(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=120)
    source_module: str = Field(default="module-42", min_length=1, max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
