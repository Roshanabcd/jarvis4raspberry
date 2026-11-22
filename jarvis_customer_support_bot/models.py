"""Typed Pydantic v1/v2 compatible schemas for Customer Support Bot."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "ChatGPT-Powered Customer Support Bot"
    version: str = "1.0.0"
    provider: str
    kb_articles: int
    open_tickets: int


class KBArticleRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    category: str = Field(default="general", max_length=60)
    content: str = Field(..., min_length=10, max_length=8000)
    tags: List[str] = Field(default_factory=list)


class KBArticleRecord(BaseModel):
    id: int
    created_at: str
    title: str
    category: str
    content: str
    tags: List[str]


class KBListResponse(BaseModel):
    total: int
    articles: List[KBArticleRecord]


class CustomerInquiryRequest(BaseModel):
    customer_name: str = Field(default="Customer", max_length=120)
    customer_email: Optional[str] = Field(default=None, max_length=160)
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=5, max_length=4000)


class TriageResult(BaseModel):
    category: str
    priority: str  # P1_CRITICAL | P2_HIGH | P3_NORMAL | P4_LOW
    sentiment: str  # POSITIVE | NEUTRAL | NEGATIVE | URGENT_FRUSTRATED
    sentiment_score: float  # -1.0 .. 1.0
    escalate: bool
    escalation_team: str
    escalation_reason: str


class SupportReplyResponse(BaseModel):
    ticket_id: int
    status: str  # open | escalated | resolved
    provider_used: str
    triage: TriageResult
    reply_text: str
    matched_kb_titles: List[str]
    confidence: float


class TicketRecord(BaseModel):
    id: int
    created_at: str
    customer_name: str
    customer_email: Optional[str] = None
    subject: str
    message: str
    category: str
    priority: str
    sentiment: str
    sentiment_score: float
    escalated: bool
    escalation_team: str
    escalation_reason: str
    status: str
    reply_text: str


class TicketListResponse(BaseModel):
    total: int
    tickets: List[TicketRecord]


class UpdateTicketRequest(BaseModel):
    status: str = Field(..., max_length=30)  # open | escalated | resolved


class SupportStatsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    escalated_tickets: int
    resolved_tickets: int
    by_category: Dict[str, int]
    by_sentiment: Dict[str, int]
