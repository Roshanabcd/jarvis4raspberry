"""SQLite (WAL mode) persistence for job descriptions and candidate match evaluations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ResumeMatchingStore:
    """Persists jobs and ranked candidate evaluations in SQLite WAL."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS rm_jobs (
                    job_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    description TEXT NOT NULL,
                    required_skills_json TEXT NOT NULL,
                    preferred_skills_json TEXT NOT NULL,
                    min_years_experience REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rm_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    candidate_name TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    recommendation_tier TEXT NOT NULL,
                    matched_required_count INTEGER NOT NULL,
                    missing_required_count INTEGER NOT NULL,
                    result_json TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES rm_jobs(job_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_rm_evals_job
                    ON rm_evaluations(job_id, overall_score DESC);
                """
            )

    @staticmethod
    def _hydrate_job(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["required_skills"] = json.loads(d.pop("required_skills_json"))
        d["preferred_skills"] = json.loads(d.pop("preferred_skills_json"))
        return d

    def create_job(
        self,
        job_id: str,
        title: str,
        company: str,
        description: str,
        required_skills: List[str],
        preferred_skills: List[str],
        min_years_experience: float,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rm_jobs
                    (job_id, created_at, title, company, description,
                     required_skills_json, preferred_skills_json, min_years_experience)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    now,
                    title,
                    company,
                    description,
                    json.dumps(required_skills, ensure_ascii=False),
                    json.dumps(preferred_skills, ensure_ascii=False),
                    min_years_experience,
                ),
            )
            row = conn.execute("SELECT * FROM rm_jobs WHERE job_id = ?", (job_id,)).fetchone()
        return self._hydrate_job(row)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM rm_jobs WHERE job_id = ?", (job_id,)).fetchone()
        return self._hydrate_job(row) if row else None

    def list_jobs(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM rm_jobs ORDER BY created_at DESC").fetchall()
        return [self._hydrate_job(r) for r in rows]

    def save_evaluation(
        self,
        job_id: str,
        candidate_name: str,
        overall_score: float,
        recommendation_tier: str,
        matched_required_count: int,
        missing_required_count: int,
        result_payload: Dict[str, Any],
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO rm_evaluations
                    (created_at, job_id, candidate_name, overall_score, recommendation_tier,
                     matched_required_count, missing_required_count, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    job_id,
                    candidate_name,
                    overall_score,
                    recommendation_tier,
                    matched_required_count,
                    missing_required_count,
                    json.dumps(result_payload, ensure_ascii=False),
                ),
            )
            return int(cur.lastrowid)

    def leaderboard(self, job_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id AS evaluation_id, created_at, candidate_name, overall_score,
                       recommendation_tier, matched_required_count, missing_required_count
                FROM rm_evaluations
                WHERE job_id = ?
                ORDER BY overall_score DESC, id DESC
                """,
                (job_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def counts(self) -> Dict[str, int]:
        with self._connect() as conn:
            jobs = int(conn.execute("SELECT COUNT(*) FROM rm_jobs").fetchone()[0])
            evals = int(conn.execute("SELECT COUNT(*) FROM rm_evaluations").fetchone()[0])
        return {"total_jobs": jobs, "total_evaluations": evals}
