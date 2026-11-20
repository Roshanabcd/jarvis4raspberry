"""FastAPI APIRouter for JARVIS Smart Resume Matching."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from .config import ResumeMatchingConfig
from .engine import ResumeMatchingEngine
from .models import (
    CreateJobRequest,
    HealthResponse,
    JobListResponse,
    JobRecord,
    LeaderboardResponse,
    MatchEvaluationResponse,
    MatchRequest,
)

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[ResumeMatchingConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = ResumeMatchingEngine(config=config)
    router = APIRouter(tags=["JARVIS Smart Resume Matching"])

    @router.get("/resume-matching", response_class=HTMLResponse, include_in_schema=False)
    def resume_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Resume Matching UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/resume-matching/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/resume-matching/jobs", response_model=JobRecord)
    def create_job(req: CreateJobRequest) -> JobRecord:
        return engine.create_job(req)

    @router.get("/api/resume-matching/jobs", response_model=JobListResponse)
    def list_jobs() -> JobListResponse:
        return engine.list_jobs()

    @router.post("/api/resume-matching/match", response_model=MatchEvaluationResponse)
    def match_candidate(req: MatchRequest) -> MatchEvaluationResponse:
        try:
            return engine.match_candidate(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/api/resume-matching/jobs/{job_id}/leaderboard", response_model=LeaderboardResponse)
    def leaderboard(job_id: str) -> LeaderboardResponse:
        try:
            return engine.leaderboard(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
