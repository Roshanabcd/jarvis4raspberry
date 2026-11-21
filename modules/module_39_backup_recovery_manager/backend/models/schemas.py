"""Pydantic v1/v2 compatible schemas for JARVIS Module 39 — Backup & Recovery Manager."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[attr-defined]
    return obj.dict()


class SnapshotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    source_rel_path: str = Field(default=".", min_length=1, max_length=256)
    notes: str = Field(default="", max_length=500)


class SnapshotRestoreRequest(BaseModel):
    target_rel_path: str = Field(..., min_length=1, max_length=256)
