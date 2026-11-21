"""Pydantic v1/v2 compatible schemas for JARVIS Module 36 — Screen Vision Assistant."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[attr-defined]
    return obj.dict()


class UIElementInput(BaseModel):
    element_id: str = Field(..., min_length=1, max_length=64)
    role: str = Field(default="button", min_length=1, max_length=40)
    label: str = Field(..., min_length=1, max_length=160)
    text: str = Field(default="", max_length=500)
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    confidence: float = Field(default=0.98, ge=0.0, le=1.0)


class CaptureCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    source: str = Field(default="desktop_primary", min_length=1, max_length=80)
    image_base64: Optional[str] = Field(default=None)
    width: Optional[int] = Field(default=None, gt=0)
    height: Optional[int] = Field(default=None, gt=0)
    ocr_text: str = Field(default="", max_length=8000)
    elements: List[UIElementInput] = Field(default_factory=list)


class ScreenQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class HitTestRequest(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
