"""SQLite (WAL mode) storage for study plans, syllabus milestones, and SM-2 flashcards."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class StudyPlannerStore:
    """Persists study plans, milestones, schedules, and spaced-repetition flashcards in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS study_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    current_level TEXT NOT NULL,
                    daily_minutes INTEGER NOT NULL,
                    days_available INTEGER NOT NULL,
                    provider_used TEXT NOT NULL,
                    schedule_json TEXT NOT NULL,
                    plan_markdown TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS study_milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER NOT NULL,
                    order_index INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    estimated_minutes INTEGER NOT NULL,
                    target_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS study_flashcards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER,
                    topic TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    repetitions INTEGER NOT NULL DEFAULT 0,
                    interval_days INTEGER NOT NULL DEFAULT 1,
                    ease_factor REAL NOT NULL DEFAULT 2.5,
                    next_review_date TEXT NOT NULL,
                    last_reviewed_at TEXT,
                    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_flashcards_next_review
                    ON study_flashcards(next_review_date);
                """
            )

    def create_plan(
        self,
        title: str,
        goal: str,
        current_level: str,
        daily_minutes: int,
        days_available: int,
        provider_used: str,
        milestones: List[Dict[str, Any]],
        schedule: List[Dict[str, Any]],
        plan_markdown: str,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO study_plans
                    (created_at, title, goal, current_level, daily_minutes, days_available,
                     provider_used, schedule_json, plan_markdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    title,
                    goal,
                    current_level,
                    daily_minutes,
                    days_available,
                    provider_used,
                    json.dumps(schedule, ensure_ascii=False),
                    plan_markdown,
                ),
            )
            plan_id = int(cur.lastrowid)
            for idx, m in enumerate(milestones, start=1):
                conn.execute(
                    """
                    INSERT INTO study_milestones
                        (plan_id, order_index, title, description, estimated_minutes, target_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                    """,
                    (
                        plan_id,
                        idx,
                        m["title"],
                        m["description"],
                        int(m["estimated_minutes"]),
                        m["target_date"],
                    ),
                )
            return plan_id

    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            plan = conn.execute("SELECT * FROM study_plans WHERE id = ?", (plan_id,)).fetchone()
            if not plan:
                return None
            milestones = conn.execute(
                "SELECT * FROM study_milestones WHERE plan_id = ? ORDER BY order_index ASC",
                (plan_id,),
            ).fetchall()
        data = dict(plan)
        data["schedule"] = json.loads(data.pop("schedule_json"))
        data["milestones"] = [dict(m) for m in milestones]
        total = len(data["milestones"])
        done = sum(1 for m in data["milestones"] if m["status"] == "completed")
        data["completion_pct"] = round((done / total) * 100.0, 1) if total else 0.0
        return data

    def list_plans(self, limit: int = 50) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT p.id, p.created_at, p.title, p.current_level, p.daily_minutes, p.days_available,
                       (SELECT COUNT(*) FROM study_milestones m WHERE m.plan_id = p.id) AS total_milestones,
                       (SELECT COUNT(*) FROM study_milestones m WHERE m.plan_id = p.id AND m.status = 'completed') AS completed_milestones
                FROM study_plans p
                ORDER BY p.id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            total = int(d["total_milestones"])
            done = int(d["completed_milestones"])
            d["completion_pct"] = round((done / total) * 100.0, 1) if total else 0.0
            out.append(d)
        return out

    def update_milestone_status(self, milestone_id: int, status: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.execute(
                "UPDATE study_milestones SET status = ? WHERE id = ?",
                (status, milestone_id),
            )
            row = conn.execute("SELECT * FROM study_milestones WHERE id = ?", (milestone_id,)).fetchone()
        return dict(row) if row else None

    def create_flashcard(
        self,
        topic: str,
        question: str,
        answer: str,
        next_review_date: str,
        plan_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO study_flashcards
                    (plan_id, topic, question, answer, repetitions, interval_days, ease_factor, next_review_date)
                VALUES (?, ?, ?, ?, 0, 1, 2.5, ?)
                """,
                (plan_id, topic, question, answer, next_review_date),
            )
            row = conn.execute("SELECT * FROM study_flashcards WHERE id = ?", (int(cur.lastrowid),)).fetchone()
        return dict(row)

    def get_flashcard(self, card_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM study_flashcards WHERE id = ?", (card_id,)).fetchone()
        return dict(row) if row else None

    def update_flashcard_sm2(
        self,
        card_id: int,
        repetitions: int,
        interval_days: int,
        ease_factor: float,
        next_review_date: str,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE study_flashcards
                SET repetitions = ?, interval_days = ?, ease_factor = ?,
                    next_review_date = ?, last_reviewed_at = ?
                WHERE id = ?
                """,
                (repetitions, interval_days, ease_factor, next_review_date, now, card_id),
            )
            row = conn.execute("SELECT * FROM study_flashcards WHERE id = ?", (card_id,)).fetchone()
        return dict(row) if row else None

    def list_flashcards(self, due_only: bool = False, today_iso: Optional[str] = None) -> List[Dict[str, Any]]:
        today = today_iso or datetime.now(timezone.utc).date().isoformat()
        with self._connect() as conn:
            if due_only:
                rows = conn.execute(
                    "SELECT * FROM study_flashcards WHERE next_review_date <= ? ORDER BY next_review_date ASC, id ASC",
                    (today,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM study_flashcards ORDER BY next_review_date ASC, id DESC"
                ).fetchall()
        return [dict(r) for r in rows]

    def progress_counts(self, today_iso: Optional[str] = None) -> Dict[str, int]:
        today = today_iso or datetime.now(timezone.utc).date().isoformat()
        with self._connect() as conn:
            plans = int(conn.execute("SELECT COUNT(*) FROM study_plans").fetchone()[0])
            milestones = int(conn.execute("SELECT COUNT(*) FROM study_milestones").fetchone()[0])
            done_ms = int(conn.execute("SELECT COUNT(*) FROM study_milestones WHERE status = 'completed'").fetchone()[0])
            cards = int(conn.execute("SELECT COUNT(*) FROM study_flashcards").fetchone()[0])
            due = int(
                conn.execute("SELECT COUNT(*) FROM study_flashcards WHERE next_review_date <= ?", (today,)).fetchone()[0]
            )
            mastered = int(
                conn.execute("SELECT COUNT(*) FROM study_flashcards WHERE repetitions >= 3 AND interval_days >= 10").fetchone()[0]
            )
        return {
            "total_plans": plans,
            "total_milestones": milestones,
            "completed_milestones": done_ms,
            "total_cards": cards,
            "due_cards_today": due,
            "mastered_cards": mastered,
        }
