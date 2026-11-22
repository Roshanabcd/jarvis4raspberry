"""Typed Pydantic v1/v2 compatible schemas for AI Social Media Automation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "AI Social Media Automation"
    version: str = "1.0.0"
    provider: str
    publish_mode: str
    total_posts: int


class PlanCampaignRequest(BaseModel):
    campaign_name: str = Field(..., min_length=3, max_length=160)
    topic: str = Field(..., min_length=3, max_length=500)
    platforms: List[str] = Field(default_factory=lambda: ["LinkedIn", "X", "Instagram", "YouTube"])
    days: int = Field(default=5, ge=1, le=14)
    tone: str = Field(default="practical, builder-focused, and engaging", max_length=120)
    call_to_action: str = Field(default="Follow for more JARVIS OS updates", max_length=200)
    start_iso_utc: Optional[str] = None


class SocialPostRecord(BaseModel):
    id: int
    created_at: str
    campaign_name: str
    platform: str
    title: str
    copy_text: str
    hashtags: List[str]
    scheduled_for: str
    status: str  # draft | scheduled | published | failed | cancelled
    published_at: Optional[str] = None
    publish_mode: Optional[str] = None
    export_path: Optional[str] = None
    character_count: int
    impressions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0


class PlanCampaignResponse(BaseModel):
    campaign_name: str
    provider_used: str
    posts_created: int
    posts: List[SocialPostRecord]
    manual_prompt_fallback: Optional[str] = None


class CreatePostRequest(BaseModel):
    campaign_name: str = Field(default="Standalone", max_length=160)
    platform: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=2, max_length=200)
    copy_text: str = Field(..., min_length=5, max_length=5000)
    hashtags: List[str] = Field(default_factory=list)
    scheduled_for: Optional[str] = None
    status: str = Field(default="scheduled", max_length=20)


class PublishPostRequest(BaseModel):
    dry_run: bool = True


class PublishResult(BaseModel):
    post_id: int
    platform: str
    dry_run: bool
    status: str
    publish_mode: str
    export_path: Optional[str] = None
    message: str


class RunDueResponse(BaseModel):
    checked_at_utc: str
    dry_run: bool
    due_count: int
    results: List[PublishResult]


class RecordMetricsRequest(BaseModel):
    impressions: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)


class PlatformAnalytics(BaseModel):
    platform: str
    posts_count: int
    published_count: int
    impressions: int
    engagements: int
    clicks: int
    engagement_rate_pct: float
    ctr_pct: float


class AnalyticsSummaryResponse(BaseModel):
    total_posts: int
    scheduled_count: int
    published_count: int
    total_impressions: int
    total_engagements: int
    total_clicks: int
    overall_engagement_rate_pct: float
    overall_ctr_pct: float
    by_platform: List[PlatformAnalytics]
    top_posts: List[SocialPostRecord]


class PostListResponse(BaseModel):
    total: int
    posts: List[SocialPostRecord]
