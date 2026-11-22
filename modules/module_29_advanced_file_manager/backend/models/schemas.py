"""Pydantic v1/v2 compatible schemas for JARVIS Module 29 — Advanced File Manager."""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class FileWriteRequest(BaseModel):
    rel_path: str = Field(..., min_length=1, max_length=260)
    content: str = Field(default="", max_length=500000)


class DirCreateRequest(BaseModel):
    rel_path: str = Field(..., min_length=1, max_length=260)


class MoveRequest(BaseModel):
    src_path: str = Field(..., min_length=1, max_length=260)
    dst_path: str = Field(..., min_length=1, max_length=260)


class TagRequest(BaseModel):
    rel_path: str = Field(..., min_length=1, max_length=260)
    tags: List[str] = Field(default_factory=list)


class OrganizeRequest(BaseModel):
    dry_run: bool = Field(default=True)
