"""Pydantic v1/v2 compatible schemas for JARVIS Module 38 — Plugin & Skills Marketplace."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[attr-defined]
    return obj.dict()


class PackagePublishRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    version: str = Field(..., min_length=5, max_length=32)
    kind: str = Field(default="skill", min_length=1, max_length=32)
    author: str = Field(default="Roshan Sharma", min_length=1, max_length=80)
    description: str = Field(default="", max_length=1000)
    permissions: List[str] = Field(default_factory=list)
    manifest_payload: str = Field(default="{}", max_length=16000)


class PackageInstallRequest(BaseModel):
    expected_sha256: Optional[str] = Field(default=None)
    enabled: bool = Field(default=True)


class PackageToggleRequest(BaseModel):
    enabled: bool
