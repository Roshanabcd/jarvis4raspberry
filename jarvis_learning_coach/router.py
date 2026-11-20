"""FastAPI APIRouter for JARVIS Personalized Learning AI Coach."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from .config import LearningCoachConfig
from .engine import LearningCoachEngine
from .models import (
    ExerciseEvaluationResponse,
    ExerciseRecord,
    GenerateExerciseRequest,
    HealthResponse,
    LearnerReplyRequest,
    LearnerReplyResponse,
    MasteryDiagnosticResponse,
    SessionResponse,
    StartSessionRequest,
    SubmitExerciseRequest,
)

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[LearningCoachConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = LearningCoachEngine(config=config)
    router = APIRouter(tags=["JARVIS Learning AI Coach"])

    @router.get("/learning-coach", response_class=HTMLResponse, include_in_schema=False)
    def coach_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Learning Coach UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/learning-coach/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/learning-coach/sessions", response_model=SessionResponse)
    def start_session(req: StartSessionRequest) -> SessionResponse:
        return engine.start_session(req)

    @router.post("/api/learning-coach/sessions/{session_id}/respond", response_model=LearnerReplyResponse)
    def respond_in_session(session_id: str, req: LearnerReplyRequest) -> LearnerReplyResponse:
        try:
            return engine.respond_in_session(session_id=session_id, req=req)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/api/learning-coach/mastery/{learner_id}", response_model=MasteryDiagnosticResponse)
    def mastery_diagnostics(learner_id: str) -> MasteryDiagnosticResponse:
        return engine.mastery_diagnostics(learner_id=learner_id)

    @router.post("/api/learning-coach/exercises/generate", response_model=ExerciseRecord)
    def generate_exercise(req: GenerateExerciseRequest) -> ExerciseRecord:
        return engine.generate_exercise(req)

    @router.post(
        "/api/learning-coach/exercises/{exercise_id}/submit",
        response_model=ExerciseEvaluationResponse,
    )
    def submit_exercise(exercise_id: str, req: SubmitExerciseRequest) -> ExerciseEvaluationResponse:
        try:
            return engine.submit_exercise(exercise_id=exercise_id, req=req)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
