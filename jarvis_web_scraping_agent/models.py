"""Typed Pydantic v1/v2 compatible schemas for Autonomous Web Scraping Agent."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Autonomous Web Scraping Agent"
    version: str = "1.0.0"
    respect_robots_txt: bool
    active_monitors: int
    total_snapshots: int


class ExtractRequest(BaseModel):
    url: Optional[str] = Field(default=None, max_length=2000)
    raw_html: Optional[str] = None
    target_tag: Optional[str] = Field(default=None, max_length=40)
    save_snapshot: bool = True


class LinkItem(BaseModel):
    text: str
    href: str


class ExtractedPage(BaseModel):
    snapshot_id: Optional[int] = None
    source: str
    content_hash: str
    title: str
    meta_description: str
    headings: List[str]
    links: List[LinkItem]
    tables: List[List[List[str]]]
    targeted_elements: List[str]
    text_preview: str
    word_count: int
    robots_allowed: bool = True


class CreateMonitorRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    url: str = Field(..., min_length=8, max_length=2000)
    target_tag: Optional[str] = Field(default=None, max_length=40)
    interval_minutes: int = Field(default=60, ge=5, le=10080)


class MonitorRecord(BaseModel):
    id: int
    created_at: str
    name: str
    url: str
    target_tag: Optional[str] = None
    interval_minutes: int
    last_checked_at: Optional[str] = None
    last_hash: Optional[str] = None
    change_count: int = 0
    status: str = "active"


class MonitorListResponse(BaseModel):
    total: int
    monitors: List[MonitorRecord]


class CheckMonitorRequest(BaseModel):
    raw_html_override: Optional[str] = None


class ChangeCheckResponse(BaseModel):
    monitor_id: int
    monitor_name: str
    url: str
    snapshot_id: int
    changed: bool
    previous_hash: Optional[str] = None
    current_hash: str
    unified_diff: str
    word_count: int


class SnapshotSummary(BaseModel):
    id: int
    created_at: str
    monitor_id: Optional[int] = None
    source: str
    title: str
    content_hash: str
    word_count: int
    changed: bool


class SnapshotListResponse(BaseModel):
    total: int
    snapshots: List[SnapshotSummary]
