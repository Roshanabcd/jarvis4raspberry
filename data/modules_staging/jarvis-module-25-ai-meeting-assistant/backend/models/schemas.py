"""Pydantic schemas for JARVIS Module 25 (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()


class MeetingCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=180)
    meeting_date: str = Field(default="2026-11-20", description="YYYY-MM-DD")
    participants: List[str] = Field(default_factory=list)
    agenda: str = Field(default="", max_length=1200)


class TranscriptSegmentRequest(BaseModel):
    speaker: str = Field(..., min_length=1, max_length=80)
    text: str = Field(..., min_length=1, max_length=4000)
    timestamp_sec: int = Field(default=0, ge=0)


class BulkTranscriptRequest(BaseModel):
    raw_transcript: str = Field(..., min_length=3, max_length=50000)


class ActionItemStatusRequest(BaseModel):
    status: str = Field(..., description="open | done | cancelled")
