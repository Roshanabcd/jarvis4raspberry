"""Pydantic schemas for JARVIS Module 20 (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AvatarPersona(str, Enum):
    ARIA = "aria"
    ATLAS = "atlas"


class SessionCreateRequest(BaseModel):
    title: str = Field(default="New JARVIS Voice Session", min_length=1, max_length=120)
    persona: AvatarPersona = Field(default=AvatarPersona.ARIA)
    system_prompt: Optional[str] = Field(default=None, max_length=1000)


class ChatMessageRequest(BaseModel):
    session_id: Optional[str] = None
    content: str = Field(..., min_length=1, max_length=4000)
    persona: AvatarPersona = Field(default=AvatarPersona.ARIA)
    simulate_provider_error: bool = Field(default=False, description="Optional test flag to verify provider error recovery")


class ProviderConfigUpdateRequest(BaseModel):
    provider: str = Field(..., min_length=2, max_length=60)
    provider_url: str = Field(default="", max_length=300)
    provider_model: str = Field(default="jarvis-local-sim-v1", max_length=120)


class VisemeCue(BaseModel):
    time_ms: int
    viseme: str
    openness: float
    word: str
