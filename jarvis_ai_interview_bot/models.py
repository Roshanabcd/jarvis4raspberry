"""Typed Pydantic v1/v2 compatible schemas for AI Interview Bot."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "AI Interview Bot"
    version: str = "1.0.0"
    provider: str
    total_sessions: int


class StartInterviewRequest(BaseModel):
    candidate_name: str = Field(default="Candidate", max_length=100)
    role: str = Field(default="Python / Backend Engineer", max_length=120)
    mode: str = Field(default="mixed", max_length=30)  # technical | behavioral | mixed
    difficulty: str = Field(default="Mid", max_length=30)  # Junior | Mid | Senior
    total_questions: int = Field(default=5, ge=2, le=10)
    focus_topics: List[str] = Field(default_factory=list)


class InterviewQuestion(BaseModel):
    turn_number: int
    category: str  # technical | behavioral
    difficulty: str
    question: str
    expected_signals: List[str] = Field(default_factory=list)


class RubricBreakdown(BaseModel):
    accuracy_depth: int
    structure_clarity: int
    problem_solving: int
    completeness: int
    overall_score: int


class AnswerEvaluation(BaseModel):
    turn_number: int
    question: str
    answer: str
    rubric: RubricBreakdown
    strengths: List[str]
    improvements: List[str]
    coaching_tip: str
    provider_used: str


class StartInterviewResponse(BaseModel):
    session_id: int
    status: str
    role: str
    mode: str
    difficulty: str
    total_questions: int
    current_question: InterviewQuestion
    provider_used: str


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=5, max_length=8000)


class SubmitAnswerResponse(BaseModel):
    session_id: int
    status: str  # in_progress | completed
    evaluation: AnswerEvaluation
    next_question: Optional[InterviewQuestion] = None
    remaining_questions: int
    manual_prompt_fallback: Optional[str] = None


class InterviewReportResponse(BaseModel):
    session_id: int
    candidate_name: str
    role: str
    mode: str
    difficulty: str
    status: str
    overall_score: int
    verdict: str
    average_rubric: RubricBreakdown
    top_strengths: List[str]
    priority_improvements: List[str]
    turns: List[AnswerEvaluation]
    report_markdown: str


class SessionSummary(BaseModel):
    id: int
    created_at: str
    candidate_name: str
    role: str
    mode: str
    difficulty: str
    status: str
    answered_count: int
    total_questions: int
    overall_score: Optional[int] = None


class SessionListResponse(BaseModel):
    total: int
    sessions: List[SessionSummary]
