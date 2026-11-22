"""Pydantic v1/v2 compatible schemas for JARVIS Module 26 — Project Autopilot."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    goal: str = Field(..., min_length=5, max_length=2000)
    tech_stack: List[str] = Field(default_factory=lambda: ["Python", "FastAPI", "SQLite"])
    dry_run: bool = Field(default=True)
    auto_plan: bool = Field(default=True)


class TaskCreateRequest(BaseModel):
    milestone_id: str = Field(..., min_length=3, max_length=64)
    title: str = Field(..., min_length=2, max_length=160)
    description: str = Field(default="", max_length=1000)
    depends_on: List[str] = Field(default_factory=list)
    requires_approval: bool = Field(default=False)
    estimated_minutes: int = Field(default=30, ge=5, le=1440)


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reviewer: str = Field(default="operator", min_length=1, max_length=80)
    note: str = Field(default="", max_length=500)


class AdvanceProjectRequest(BaseModel):
    max_steps: int = Field(default=3, ge=1, le=20)
    dry_run: Optional[bool] = Field(default=None)


class ScaffoldRequest(BaseModel):
    include_tests: bool = Field(default=True)
