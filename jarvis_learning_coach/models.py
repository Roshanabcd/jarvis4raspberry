"""Pydantic v1/v2 compatible schemas for JARVIS Personalized Learning AI Coach."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Personalized Learning AI Coach"
    version: str = "1.0.0"
    total_sessions: int
    total_exercises: int
    tracked_concepts: int


class StartSessionRequest(BaseModel):
    learner_id: str = Field(..., min_length=1, max_length=120)
    subject: str = Field(..., min_length=2, max_length=120)
    concept: str = Field(..., min_length=2, max_length=160)
    goal: str = Field(default="Build deep conceptual understanding", max_length=400)


class CoachTurn(BaseModel):
    turn_index: int
    role: str  # coach | learner
    message: str
    hint_level: int = 0


class SessionResponse(BaseModel):
    session_id: str
    learner_id: str
    subject: str
    concept: str
    difficulty_tier: str
    mastery_score: float
    turns: List[CoachTurn]


class LearnerReplyRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=3000)
    request_hint: bool = False
    use_llm: bool = False


class LearnerReplyResponse(BaseModel):
    session_id: str
    coach_reply: str
    mode: str
    hint_level: int
    mastery_score: float
    mastery_delta: float
    difficulty_tier: str
    understanding_signal: str


class ConceptMasteryRecord(BaseModel):
    learner_id: str
    subject: str
    concept: str
    mastery_score: float
    difficulty_tier: str
    attempts: int
    streak: int
    updated_at: str


class MasteryDiagnosticResponse(BaseModel):
    learner_id: str
    overall_mastery: float
    strengths: List[str]
    focus_gaps: List[str]
    recommended_next_concept: Optional[str] = None
    concepts: List[ConceptMasteryRecord]


class GenerateExerciseRequest(BaseModel):
    learner_id: str = Field(..., min_length=1, max_length=120)
    subject: str = Field(..., min_length=2, max_length=120)
    concept: str = Field(..., min_length=2, max_length=160)


class ExerciseRecord(BaseModel):
    exercise_id: str
    learner_id: str
    subject: str
    concept: str
    difficulty_tier: str
    prompt: str
    hint: str
    expected_keywords: List[str]
    created_at: str


class SubmitExerciseRequest(BaseModel):
    answer: str = Field(..., min_length=2, max_length=4000)


class ExerciseEvaluationResponse(BaseModel):
    exercise_id: str
    score: float
    passed: bool
    covered_concepts: List[str]
    missing_concepts: List[str]
    feedback: str
    updated_mastery: float
    difficulty_tier: str
