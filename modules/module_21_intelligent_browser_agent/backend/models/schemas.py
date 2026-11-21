"""Pydantic schemas for JARVIS Module 21 (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()


class SessionCreateRequest(BaseModel):
    name: str = Field(default="JARVIS Browser Session", min_length=1, max_length=100)
    start_url: str = Field(default="https://docs.jarvis.local/overview", max_length=500)


class NavigateRequest(BaseModel):
    url: str = Field(..., min_length=4, max_length=1000)


class FormFillRequest(BaseModel):
    form_id: str = Field(..., min_length=1, max_length=100)
    fields: Dict[str, str] = Field(default_factory=dict)


class FormSubmitRequest(BaseModel):
    form_id: str = Field(..., min_length=1, max_length=100)
    fields: Dict[str, str] = Field(default_factory=dict)
    requested_by: str = Field(default="operator", min_length=1, max_length=80)


class WorkflowStep(BaseModel):
    action: str = Field(..., description="navigate | inspect | extract_dom | screenshot | fill_form | submit_form | download")
    params: Dict[str, Any] = Field(default_factory=dict)


class WorkflowCreateRequest(BaseModel):
    session_id: Optional[str] = None
    name: str = Field(default="Multi-Page Browser Workflow", min_length=1, max_length=120)
    steps: List[WorkflowStep] = Field(..., min_items=1, max_items=30)
    requested_by: str = Field(default="operator", min_length=1, max_length=80)


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    decided_by: str = Field(default="operator", min_length=1, max_length=80)
    comment: str = Field(default="", max_length=500)


class SitePolicyUpdateRequest(BaseModel):
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None
    require_approval_for_form_submit: Optional[bool] = None
    allow_downloads: Optional[bool] = None
