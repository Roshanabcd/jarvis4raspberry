"""Core Smart Resume Matching service orchestrating job profiles, candidate matching, and leaderboards."""

from __future__ import annotations

import uuid
from typing import Optional

from .config import ResumeMatchingConfig
from .extractor import extract_skills, extract_years_experience, normalize_skill
from .matcher import evaluate_candidate_match
from .models import (
    CreateJobRequest,
    HealthResponse,
    JobListResponse,
    JobRecord,
    LeaderboardEntry,
    LeaderboardResponse,
    MatchEvaluationResponse,
    MatchRequest,
)
from .storage import ResumeMatchingStore


class ResumeMatchingEngine:
    """Manages job postings, candidate skill extraction, qualification scoring, and gap analysis."""

    def __init__(self, config: Optional[ResumeMatchingConfig] = None) -> None:
        self.config = config or ResumeMatchingConfig()
        self.store = ResumeMatchingStore(self.config.db_path)

    def health(self) -> HealthResponse:
        c = self.store.counts()
        return HealthResponse(
            total_jobs=c["total_jobs"],
            total_evaluations=c["total_evaluations"],
        )

    def create_job(self, req: CreateJobRequest) -> JobRecord:
        req_skills = sorted({normalize_skill(s) for s in req.required_skills if s.strip()})
        if not req_skills:
            req_skills = extract_skills(req.description)
        pref_skills = sorted({normalize_skill(s) for s in req.preferred_skills if s.strip()} - set(req_skills))
        min_years = req.min_years_experience or extract_years_experience(req.description)

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        saved = self.store.create_job(
            job_id=job_id,
            title=req.title.strip(),
            company=req.company.strip() or "Internal",
            description=req.description.strip(),
            required_skills=req_skills,
            preferred_skills=pref_skills,
            min_years_experience=min_years,
        )
        return JobRecord(**saved)

    def list_jobs(self) -> JobListResponse:
        jobs = [JobRecord(**j) for j in self.store.list_jobs()]
        return JobListResponse(total=len(jobs), jobs=jobs)

    def match_candidate(self, req: MatchRequest) -> MatchEvaluationResponse:
        job_id: Optional[str] = None
        if req.job_id:
            job = self.store.get_job(req.job_id.strip())
            if job is None:
                raise KeyError(f"Job '{req.job_id}' not found.")
            job_id = job["job_id"]
            job_title = job["title"]
            jd_text = job["description"]
            req_skills = job["required_skills"]
            pref_skills = job["preferred_skills"]
            min_years = float(job["min_years_experience"])
        else:
            if not req.job_description or not req.job_description.strip():
                raise ValueError("Provide either 'job_id' or an inline 'job_description'.")
            job_title = (req.job_title or "Ad-Hoc Role").strip()
            jd_text = req.job_description.strip()
            req_skills = req.required_skills
            pref_skills = req.preferred_skills
            min_years = (
                req.min_years_experience
                if req.min_years_experience is not None
                else extract_years_experience(jd_text)
            )

        result = evaluate_candidate_match(
            resume_text=req.resume_text,
            job_description=jd_text,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            min_years_experience=min_years,
            config=self.config,
        )

        eval_id: Optional[int] = None
        if job_id is not None:
            eval_id = self.store.save_evaluation(
                job_id=job_id,
                candidate_name=req.candidate_name.strip(),
                overall_score=float(result["overall_score"]),
                recommendation_tier=str(result["recommendation_tier"]),
                matched_required_count=len(result["matched_required_skills"]),  # type: ignore[arg-type]
                missing_required_count=len(result["missing_required_skills"]),  # type: ignore[arg-type]
                result_payload=result,
            )

        return MatchEvaluationResponse(
            evaluation_id=eval_id,
            job_id=job_id,
            job_title=job_title,
            candidate_name=req.candidate_name.strip(),
            **result,  # type: ignore[arg-type]
        )

    def leaderboard(self, job_id: str) -> LeaderboardResponse:
        job = self.store.get_job(job_id.strip())
        if job is None:
            raise KeyError(f"Job '{job_id}' not found.")
        rows = [LeaderboardEntry(**r) for r in self.store.leaderboard(job["job_id"])]
        return LeaderboardResponse(
            job_id=job["job_id"],
            job_title=job["title"],
            total_candidates=len(rows),
            candidates=rows,
        )
