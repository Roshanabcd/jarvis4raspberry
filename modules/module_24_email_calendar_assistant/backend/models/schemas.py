"""Pydantic schemas for JARVIS Module 24 (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()


class EmailIngestRequest(BaseModel):
    sender: str = Field(..., min_length=3, max_length=160)
    recipient: str = Field(default="operator@jarvis.local", max_length=160)
    subject: str = Field(..., min_length=1, max_length=240)
    body: str = Field(..., min_length=1, max_length=12000)


class DraftCreateRequest(BaseModel):
    to_address: str = Field(..., min_length=3, max_length=160)
    subject: str = Field(..., min_length=1, max_length=240)
    body: str = Field(..., min_length=1, max_length=12000)
    in_reply_to: Optional[str] = None


class DraftReplyOptions(BaseModel):
    tone: str = Field(default="professional", description="professional | concise | friendly")
    extra_notes: str = Field(default="", max_length=500)


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    decided_by: str = Field(default="operator", min_length=1, max_length=80)
    comment: str = Field(default="", max_length=400)


class CalendarEventCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=180)
    date: str = Field(..., description="YYYY-MM-DD")
    start_time: str = Field(..., description="HH:MM")
    end_time: str = Field(..., description="HH:MM")
    location: str = Field(default="", max_length=160)
    attendees: List[str] = Field(default_factory=list)
    description: str = Field(default="", max_length=1000)
    allow_overlap: bool = Field(default=False)


class CalendarRsvpRequest(BaseModel):
    rsvp_status: str = Field(..., description="accepted | tentative | declined | cancelled")


class FreeSlotsRequest(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    duration_minutes: int = Field(default=30, ge=10, le=480)
