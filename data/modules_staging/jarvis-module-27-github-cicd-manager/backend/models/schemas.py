"""Pydantic v1/v2 compatible schemas for JARVIS Module 27 — GitHub & CI/CD Manager."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class RepoCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=140, description="owner/repo")
    default_branch: str = Field(default="main", min_length=1, max_length=60)
    require_ci_green: bool = Field(default=True)
    workflows: List[str] = Field(default_factory=lambda: ["ci-test", "security-scan", "build-release"])


class PRCreateRequest(BaseModel):
    repo_id: str = Field(..., min_length=3, max_length=64)
    title: str = Field(..., min_length=3, max_length=200)
    source_branch: str = Field(..., min_length=1, max_length=80)
    target_branch: str = Field(default="main", min_length=1, max_length=80)
    author: str = Field(default="roshan", min_length=1, max_length=80)
    files_changed: int = Field(default=4, ge=1, le=5000)


class PipelineTriggerRequest(BaseModel):
    repo_id: str = Field(..., min_length=3, max_length=64)
    workflow_name: str = Field(default="ci-test", min_length=2, max_length=80)
    branch: str = Field(default="main", min_length=1, max_length=80)
    pr_id: Optional[str] = Field(default=None)
    simulate_failure: bool = Field(default=False)


class MergePRRequest(BaseModel):
    strategy: Literal["squash", "merge", "rebase"] = Field(default="squash")
    merged_by: str = Field(default="operator", min_length=1, max_length=80)


class ReleaseCreateRequest(BaseModel):
    repo_id: str = Field(..., min_length=3, max_length=64)
    tag_name: str = Field(..., min_length=2, max_length=40)
    notes: str = Field(default="", max_length=2000)
