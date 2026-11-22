"""Pydantic v1/v2 compatible schemas for JARVIS Smart Resume Matching."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Smart Resume Matching"
    version: str = "1.0.0"
    total_jobs: int
    total_evaluations: int


class CreateJobRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    company: str = Field(default="Internal", max_length=160)
    description: str = Field(..., min_length=15, max_length=20000)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_years_experience: float = Field(default=0.0, ge=0.0, le=40.0)


class JobRecord(BaseModel):
    job_id: str
    created_at: str
    title: str
    company: str
    description: str
    required_skills: List[str]
    preferred_skills: List[str]
    min_years_experience: float


class JobListResponse(BaseModel):
    total: int
    jobs: List[JobRecord]


class MatchRequest(BaseModel):
    candidate_name: str = Field(..., min_length=1, max_length=160)
    resume_text: str = Field(..., min_length=20, max_length=40000)
    job_id: Optional[str] = None
    job_title: Optional[str] = Field(default=None, max_length=200)
    job_description: Optional[str] = Field(default=None, max_length=20000)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_years_experience: Optional[float] = Field(default=None, ge=0.0, le=40.0)


class MatchEvaluationResponse(BaseModel):
    evaluation_id: Optional[int] = None
    job_id: Optional[str] = None
    job_title: str
    candidate_name: str
    overall_score: float
    required_skill_score: float
    preferred_skill_score: float
    semantic_similarity: float
    experience_score: float
    recommendation_tier: str
    extracted_candidate_skills: List[str]
    candidate_years_experience: float
    candidate_education: str
    matched_required_skills: List[str]
    missing_required_skills: List[str]
    matched_preferred_skills: List[str]
    missing_preferred_skills: List[str]
    gap_recommendations: List[str]


class LeaderboardEntry(BaseModel):
    evaluation_id: int
    created_at: str
    candidate_name: str
    overall_score: float
    recommendation_tier: str
    matched_required_count: int
    missing_required_count: int


class LeaderboardResponse(BaseModel):
    job_id: str
    job_title: str
    total_candidates: int
    candidates: List[LeaderboardEntry]
