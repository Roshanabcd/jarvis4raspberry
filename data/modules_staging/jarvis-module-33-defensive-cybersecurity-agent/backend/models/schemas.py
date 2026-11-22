"""Pydantic v1/v2 compatible schemas for JARVIS Module 33 — Defensive Cybersecurity Agent."""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class SecretScanRequest(BaseModel):
    relative_path: str = Field(default=".", max_length=256)


class FimBaselineRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    relative_path: str = Field(default=".", max_length=256)


class LogAnalyzeRequest(BaseModel):
    source: str = Field(default="auth.log", min_length=2, max_length=80)
    lines: List[str] = Field(..., min_items=1, max_items=2000)


class IncidentResolveRequest(BaseModel):
    resolution_note: str = Field(..., min_length=2, max_length=300)
