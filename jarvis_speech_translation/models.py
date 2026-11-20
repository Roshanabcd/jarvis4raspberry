"""Pydantic v1/v2 compatible schemas for JARVIS Real-Time Speech Translation."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "ne": "Nepali",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
}


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Real-Time Speech Translation"
    version: str = "1.0.0"
    supported_languages: Dict[str, str]
    local_tts_available: bool
    total_sessions: int
    total_utterances: int


class CreateSessionRequest(BaseModel):
    title: str = Field(default="Bilingual Conversation", min_length=1, max_length=160)
    lang_a: str = Field(default="en", min_length=2, max_length=10)
    lang_b: str = Field(default="ne", min_length=2, max_length=10)


class UtteranceRecord(BaseModel):
    id: int
    session_id: str
    created_at: str
    speaker: str
    source_lang: str
    target_lang: str
    source_text: str
    translated_text: str
    provider: str
    latency_ms: float


class SessionDetailResponse(BaseModel):
    session_id: str
    created_at: str
    title: str
    lang_a: str
    lang_b: str
    utterances: List[UtteranceRecord]


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    source_lang: str = Field(default="auto", min_length=2, max_length=10)
    target_lang: str = Field(default="ne", min_length=2, max_length=10)
    session_id: Optional[str] = None
    speaker: str = Field(default="speaker_a", max_length=64)
    use_llm: bool = False


class TranslateResponse(BaseModel):
    source_lang: str
    target_lang: str
    source_text: str
    translated_text: str
    provider: str
    latency_ms: float
    tts_bcp47: str
    utterance_id: Optional[int] = None


class GlossaryEntryRequest(BaseModel):
    source_lang: str = Field(..., min_length=2, max_length=10)
    target_lang: str = Field(..., min_length=2, max_length=10)
    source_term: str = Field(..., min_length=1, max_length=160)
    target_term: str = Field(..., min_length=1, max_length=160)


class GlossaryEntryRecord(BaseModel):
    id: int
    source_lang: str
    target_lang: str
    source_term: str
    target_term: str


class GlossaryListResponse(BaseModel):
    total: int
    entries: List[GlossaryEntryRecord]
