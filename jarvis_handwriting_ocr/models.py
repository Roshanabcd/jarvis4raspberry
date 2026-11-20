"""Pydantic v1/v2 compatible schemas for JARVIS Handwritten to Text Converter."""

from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Handwritten to Text Converter"
    version: str = "1.0.0"
    backends: Dict[str, bool]
    total_conversions: int


class ConvertImageRequest(BaseModel):
    filename: str = Field(default="handwriting.png", min_length=1, max_length=200)
    image_base64: str = Field(..., min_length=16, max_length=15_000_000)
    language: str = Field(default="eng", min_length=2, max_length=24)
    preprocess: bool = True
    cleanup_text: bool = True
    use_vision_llm: bool = False


class ConversionRecord(BaseModel):
    id: int
    created_at: str
    filename: str
    width: int
    height: int
    engine_used: str
    language: str
    raw_text: str
    cleaned_text: str
    word_count: int
    char_count: int
    confidence: float
    latency_ms: float


class HistoryListResponse(BaseModel):
    total: int
    items: List[ConversionRecord]


class DeleteConversionResponse(BaseModel):
    deleted: bool
    conversion_id: int
