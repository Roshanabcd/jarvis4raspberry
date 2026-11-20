"""Typed Pydantic v1/v2 compatible schemas for AI Content Creation Pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "AI Content Creation Pipeline"
    version: str = "1.0.0"
    provider: str
    saved_items: int


class BlogRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    audience: str = Field(default="developers and robotics builders", max_length=200)
    tone: str = Field(default="practical, clear, and technical", max_length=120)
    target_words: int = Field(default=800, ge=250, le=3000)
    key_points: List[str] = Field(default_factory=list)
    include_code_example: bool = True


class BlogResponse(BaseModel):
    item_id: int
    provider_used: str
    title: str
    meta_description: str
    estimated_read_minutes: int
    tags: List[str]
    markdown: str
    manual_prompt_fallback: Optional[str] = None


class VideoScriptRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    platform: str = Field(default="YouTube Shorts", max_length=60)
    duration_seconds: int = Field(default=60, ge=15, le=180)
    audience: str = Field(default="tech enthusiasts and builders", max_length=200)
    tone: str = Field(default="energetic, concise, and visual", max_length=120)
    call_to_action: str = Field(default="Follow for more JARVIS OS builds", max_length=200)


class VideoScene(BaseModel):
    timestamp: str
    segment: str
    spoken_line: str
    visual_cue: str


class VideoScriptResponse(BaseModel):
    item_id: int
    provider_used: str
    title: str
    platform: str
    duration_seconds: int
    scenes: List[VideoScene]
    full_script_markdown: str
    manual_prompt_fallback: Optional[str] = None


class HooksCaptionsRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    platforms: List[str] = Field(default_factory=lambda: ["YouTube", "LinkedIn", "Instagram", "X"])
    tone: str = Field(default="engaging and authentic", max_length=120)
    hook_count: int = Field(default=5, ge=3, le=12)
    call_to_action: str = Field(default="Drop a comment if you want the full architecture", max_length=200)


class HookItem(BaseModel):
    style: str
    text: str


class PlatformCaption(BaseModel):
    platform: str
    caption: str
    hashtags: List[str]
    character_count: int


class HooksCaptionsResponse(BaseModel):
    item_id: int
    provider_used: str
    topic: str
    hooks: List[HookItem]
    captions: List[PlatformCaption]
    markdown: str
    manual_prompt_fallback: Optional[str] = None


class CarouselRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    platform: str = Field(default="LinkedIn / Instagram", max_length=80)
    slide_count: int = Field(default=7, ge=4, le=12)
    audience: str = Field(default="engineers and creators", max_length=200)
    tone: str = Field(default="crisp, visual, and actionable", max_length=120)


class CarouselSlide(BaseModel):
    slide_number: int
    role: str
    headline: str
    body: str
    visual_note: str


class CarouselResponse(BaseModel):
    item_id: int
    provider_used: str
    topic: str
    platform: str
    slides: List[CarouselSlide]
    markdown: str
    manual_prompt_fallback: Optional[str] = None


class CampaignRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    audience: str = Field(default="developers and makers", max_length=200)
    tone: str = Field(default="practical, clear, and energetic", max_length=120)
    video_duration_seconds: int = Field(default=60, ge=15, le=180)
    carousel_slides: int = Field(default=7, ge=4, le=12)
    call_to_action: str = Field(default="Follow along as we build JARVIS OS step by step", max_length=200)


class CampaignResponse(BaseModel):
    campaign_id: int
    topic: str
    blog: BlogResponse
    video_script: VideoScriptResponse
    hooks_captions: HooksCaptionsResponse
    carousel: CarouselResponse
    combined_markdown: str


class LibraryItemSummary(BaseModel):
    id: int
    created_at: str
    content_type: str
    title: str
    provider: str
    topic: str


class LibraryListResponse(BaseModel):
    total: int
    items: List[LibraryItemSummary]


class LibraryItemDetail(BaseModel):
    id: int
    created_at: str
    content_type: str
    title: str
    provider: str
    topic: str
    markdown: str
    payload: Dict[str, Any]
