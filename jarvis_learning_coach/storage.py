"""SQLite (WAL mode) persistence for coaching sessions, concept mastery, and exercises."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class LearningCoachStore:
    """Stores Socratic tutoring sessions, concept mastery diagnostics, and exercises in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS coach_mastery (
                    learner_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    mastery_score REAL NOT NULL,
                    difficulty_tier TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    streak INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (learner_id, subject, concept)
                );

                CREATE TABLE IF NOT EXISTS coach_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    goal TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS coach_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    hint_level INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES coach_sessions(session_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS coach_exercises (
                    exercise_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    difficulty_tier TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    hint TEXT NOT NULL,
                    expected_keywords_json TEXT NOT NULL,
                    model_solution TEXT NOT NULL
                );
                """
            )

    def get_or_init_mastery(self, learner_id: str, subject: str, concept: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM coach_mastery
                WHERE learner_id = ? AND subject = ? AND concept = ?
                """,
                (learner_id, subject, concept),
            ).fetchone()
            if row:
                return dict(row)
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO coach_mastery
                    (learner_id, subject, concept, mastery_score, difficulty_tier, attempts, streak, updated_at)
                VALUES (?, ?, ?, 35.0, 'foundational', 0, 0, ?)
                """,
                (learner_id, subject, concept, now),
            )
            row = conn.execute(
                """
                SELECT * FROM coach_mastery
                WHERE learner_id = ? AND subject = ? AND concept = ?
                """,
                (learner_id, subject, concept),
            ).fetchone()
        return dict(row)

    def update_mastery(
        self,
        learner_id: str,
        subject: str,
        concept: str,
        new_score: float,
        tier: str,
        attempts: int,
        streak: int,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO coach_mastery
                    (learner_id, subject, concept, mastery_score, difficulty_tier, attempts, streak, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_id, subject, concept) DO UPDATE SET
                    mastery_score = excluded.mastery_score,
                    difficulty_tier = excluded.difficulty_tier,
                    attempts = excluded.attempts,
                    streak = excluded.streak,
                    updated_at = excluded.updated_at
                """,
                (learner_id, subject, concept, round(new_score, 2), tier, attempts, streak, now),
            )
            row = conn.execute(
                """
                SELECT * FROM coach_mastery
                WHERE learner_id = ? AND subject = ? AND concept = ?
                """,
                (learner_id, subject, concept),
            ).fetchone()
        return dict(row)

    def list_mastery(self, learner_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM coach_mastery
                WHERE learner_id = ?
                ORDER BY mastery_score ASC, updated_at DESC
                """,
                (learner_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_session(
        self,
        session_id: str,
        learner_id: str,
        subject: str,
        concept: str,
        goal: str,
        opening_prompt: str,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO coach_sessions (session_id, created_at, learner_id, subject, concept, goal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, now, learner_id, subject, concept, goal),
            )
            conn.execute(
                """
                INSERT INTO coach_turns (session_id, turn_index, role, message, hint_level, created_at)
                VALUES (?, 0, 'coach', ?, 0, ?)
                """,
                (session_id, opening_prompt, now),
            )
        return self.get_session(session_id)  # type: ignore[return-value]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            srow = conn.execute(
                "SELECT * FROM coach_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not srow:
                return None
            trows = conn.execute(
                "SELECT turn_index, role, message, hint_level FROM coach_turns WHERE session_id = ? ORDER BY turn_index ASC",
                (session_id,),
            ).fetchall()
        d = dict(srow)
        d["turns"] = [dict(t) for t in trows]
        return d

    def append_turn(self, session_id: str, role: str, message: str, hint_level: int = 0) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            max_idx = conn.execute(
                "SELECT COALESCE(MAX(turn_index), -1) FROM coach_turns WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO coach_turns (session_id, turn_index, role, message, hint_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, int(max_idx) + 1, role, message, hint_level, now),
            )

    def save_exercise(self, ex: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO coach_exercises
                    (exercise_id, created_at, learner_id, subject, concept, difficulty_tier,
                     prompt, hint, expected_keywords_json, model_solution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ex["exercise_id"],
                    now,
                    ex["learner_id"],
                    ex["subject"],
                    ex["concept"],
                    ex["difficulty_tier"],
                    ex["prompt"],
                    ex["hint"],
                    json.dumps(ex["expected_keywords"], ensure_ascii=False),
                    ex["model_solution"],
                ),
            )
            row = conn.execute(
                "SELECT * FROM coach_exercises WHERE exercise_id = ?", (ex["exercise_id"],)
            ).fetchone()
        d = dict(row)
        d["expected_keywords"] = json.loads(d.pop("expected_keywords_json"))
        return d

    def get_exercise(self, exercise_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM coach_exercises WHERE exercise_id = ?", (exercise_id,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["expected_keywords"] = json.loads(d.pop("expected_keywords_json"))
        return d

    def counts(self) -> Dict[str, int]:
        with self._connect() as conn:
            sessions = int(conn.execute("SELECT COUNT(*) FROM coach_sessions").fetchone()[0])
            exercises = int(conn.execute("SELECT COUNT(*) FROM coach_exercises").fetchone()[0])
            concepts = int(conn.execute("SELECT COUNT(*) FROM coach_mastery").fetchone()[0])
        return {
            "total_sessions": sessions,
            "total_exercises": exercises,
            "tracked_concepts": concepts,
        }
