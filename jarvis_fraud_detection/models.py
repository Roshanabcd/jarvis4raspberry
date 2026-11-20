"""Pydantic v1/v2 compatible schemas for JARVIS Fraud Detection System."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

VALID_STREAMS = {"transaction", "auth_log", "audit_entry"}
VALID_ALERT_STATUSES = {"open", "investigating", "resolved", "false_positive"}


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Fraud Detection System"
    version: str = "1.0.0"
    total_events: int
    open_alerts: int


class SecurityEventRequest(BaseModel):
    stream_type: str = Field(..., max_length=40)  # transaction | auth_log | audit_entry
    actor_id: str = Field(..., min_length=1, max_length=120)
    action: str = Field(default="transfer", max_length=120)
    status: str = Field(default="success", max_length=40)  # success | failed | denied
    amount: Optional[float] = Field(default=None, ge=0.0)
    ip_address: Optional[str] = Field(default=None, max_length=64)
    geo_country: Optional[str] = Field(default=None, max_length=64)
    device_id: Optional[str] = Field(default=None, max_length=120)
    event_time: Optional[str] = Field(default=None, max_length=64)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SignalDetail(BaseModel):
    code: str
    weight: float
    detail: str


class ScoredEventRecord(BaseModel):
    id: int
    created_at: str
    event_time: str
    stream_type: str
    actor_id: str
    action: str
    status: str
    amount: Optional[float] = None
    ip_address: Optional[str] = None
    geo_country: Optional[str] = None
    device_id: Optional[str] = None
    risk_score: float
    severity: str
    decision: str
    signals: List[SignalDetail]
    alert_id: Optional[int] = None


class BatchEventsRequest(BaseModel):
    events: List[SecurityEventRequest] = Field(..., min_length=1, max_length=200)


class BatchEventsResponse(BaseModel):
    processed: int
    alerts_created: int
    results: List[ScoredEventRecord]


class EventListResponse(BaseModel):
    total: int
    events: List[ScoredEventRecord]


class AlertRecord(BaseModel):
    id: int
    created_at: str
    updated_at: str
    event_id: int
    stream_type: str
    actor_id: str
    risk_score: float
    severity: str
    decision: str
    status: str
    analyst_note: str
    signals: List[SignalDetail]


class AlertListResponse(BaseModel):
    total: int
    alerts: List[AlertRecord]


class AlertUpdateRequest(BaseModel):
    status: str = Field(..., max_length=40)
    analyst_note: str = Field(default="", max_length=1000)


class ActorRiskSummary(BaseModel):
    actor_id: str
    event_count: int
    avg_risk_score: float
    max_risk_score: float


class AnalyticsSummaryResponse(BaseModel):
    total_events: int
    total_alerts: int
    open_alerts: int
    by_stream_type: Dict[str, int]
    by_severity: Dict[str, int]
    top_risky_actors: List[ActorRiskSummary]
