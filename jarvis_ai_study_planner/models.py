"""Typed Pydantic v1/v2 compatible schemas for AI Study Planner."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "AI Study Planner"
    version: str = "1.0.0"
    provider: str
    total_plans: int
    due_reviews: int


class CreateStudyPlanRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    goal: str = Field(..., min_length=5, max_length=1000)
    syllabus_topics: List[str] = Field(default_factory=list)
    daily_minutes: int = Field(default=60, ge=15, le=480)
    days_available: int = Field(default=14, ge=3, le=180)
    current_level: str = Field(default="Intermediate", max_length=40)
    start_date: Optional[str] = None  # YYYY-MM-DD


class MilestoneItem(BaseModel):
    id: int
    plan_id: int
    order_index: int
    title: str
    description: str
    estimated_minutes: int
    target_date: str
    status: str  # pending | in_progress | completed


class StudyBlock(BaseModel):
    day_number: int
    date: str
    focus_topic: str
    minutes: int
    activity_type: str  # deep_study | practice | spaced_review


class StudyPlanDetail(BaseModel):
    id: int
    created_at: str
    title: str
    goal: str
    current_level: str
    daily_minutes: int
    days_available: int
    provider_used: str
    completion_pct: float
    milestones: List[MilestoneItem]
    schedule: List[StudyBlock]
    plan_markdown: str


class PlanSummary(BaseModel):
    id: int
    created_at: str
    title: str
    current_level: str
    daily_minutes: int
    days_available: int
    completed_milestones: int
    total_milestones: int
    completion_pct: float


class PlanListResponse(BaseModel):
    total: int
    plans: List[PlanSummary]


class UpdateMilestoneRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|in_progress|completed)$")


class CreateFlashcardRequest(BaseModel):
    plan_id: Optional[int] = None
    topic: str = Field(..., min_length=2, max_length=150)
    question: str = Field(..., min_length=3, max_length=1000)
    answer: str = Field(..., min_length=1, max_length=2000)


class FlashcardRecord(BaseModel):
    id: int
    plan_id: Optional[int] = None
    topic: str
    question: str
    answer: str
    repetitions: int
    interval_days: int
    ease_factor: float
    next_review_date: str
    last_reviewed_at: Optional[str] = None


class FlashcardListResponse(BaseModel):
    total: int
    cards: List[FlashcardRecord]


class ReviewFlashcardRequest(BaseModel):
    quality: int = Field(..., ge=0, le=5)  # SM-2 scale: 0 (blackout) to 5 (perfect recall)


class StudyProgressResponse(BaseModel):
    total_plans: int
    total_milestones: int
    completed_milestones: int
    overall_completion_pct: float
    total_cards: int
    due_cards_today: int
    mastered_cards: int
