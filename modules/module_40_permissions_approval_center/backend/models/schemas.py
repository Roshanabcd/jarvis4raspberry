"""Pydantic v1/v2 compatible schemas for JARVIS Module 40 — Permissions & Approval Center."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[attr-defined]
    return obj.dict()


class PolicyUpsertRequest(BaseModel):
    module_id: str = Field(..., min_length=1, max_length=80)
    action: str = Field(..., min_length=1, max_length=80)
    risk_level: str = Field(default="medium", min_length=1, max_length=20)
    mode: str = Field(default="require_approval", min_length=1, max_length=32)
    description: str = Field(default="", max_length=500)


class ApprovalSubmitRequest(BaseModel):
    requester: str = Field(..., min_length=1, max_length=80)
    module_id: str = Field(..., min_length=1, max_length=80)
    action: str = Field(..., min_length=1, max_length=80)
    risk_level: str = Field(default="high", min_length=1, max_length=20)
    summary: str = Field(..., min_length=1, max_length=500)
    payload: Dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int = Field(default=600, ge=0, le=86400)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., min_length=1, max_length=20)
    reviewer: str = Field(default="Roshan Sharma", min_length=1, max_length=80)
    rationale: str = Field(default="", max_length=500)
