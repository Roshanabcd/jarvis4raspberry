"""SQLite (WAL mode) persistence for interview sessions, turns, and evaluations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class InterviewBotStore:
    """Stores interactive interview sessions and turn-by-turn evaluations in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS interview_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    candidate_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    total_questions INTEGER NOT NULL,
                    focus_topics_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    overall_score INTEGER,
                    report_markdown TEXT
                );

                CREATE TABLE IF NOT EXISTS interview_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    turn_number INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    question TEXT NOT NULL,
                    expected_signals_json TEXT NOT NULL,
                    answer TEXT,
                    evaluation_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_interview_turns_session
                    ON interview_turns(session_id, turn_number);
                """
            )

    def create_session(
        self,
        candidate_name: str,
        role: str,
        mode: str,
        difficulty: str,
        total_questions: int,
        focus_topics: List[str],
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO interview_sessions
                    (created_at, candidate_name, role, mode, difficulty, total_questions, focus_topics_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'in_progress')
                """,
                (
                    now,
                    candidate_name,
                    role,
                    mode,
                    difficulty,
                    total_questions,
                    json.dumps(focus_topics, ensure_ascii=False),
                ),
            )
            return int(cur.lastrowid)

    def add_question_turn(
        self,
        session_id: int,
        turn_number: int,
        category: str,
        difficulty: str,
        question: str,
        expected_signals: List[str],
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO interview_turns
                    (session_id, turn_number, category, difficulty, question, expected_signals_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    turn_number,
                    category,
                    difficulty,
                    question,
                    json.dumps(expected_signals, ensure_ascii=False),
                    now,
                ),
            )
            return int(cur.lastrowid)

    def record_answer(
        self,
        session_id: int,
        turn_number: int,
        answer: str,
        evaluation: Dict[str, Any],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE interview_turns
                SET answer = ?, evaluation_json = ?
                WHERE session_id = ? AND turn_number = ?
                """,
                (answer, json.dumps(evaluation, ensure_ascii=False), session_id, turn_number),
            )

    def complete_session(self, session_id: int, overall_score: int, report_markdown: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE interview_sessions
                SET status = 'completed', overall_score = ?, report_markdown = ?
                WHERE id = ?
                """,
                (overall_score, report_markdown, session_id),
            )

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM interview_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["focus_topics"] = json.loads(data.pop("focus_topics_json"))
        return data

    def get_turns(self, session_id: int) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM interview_turns
                WHERE session_id = ?
                ORDER BY turn_number ASC
                """,
                (session_id,),
            ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            item = dict(r)
            item["expected_signals"] = json.loads(item.pop("expected_signals_json"))
            raw_eval = item.pop("evaluation_json")
            item["evaluation"] = json.loads(raw_eval) if raw_eval else None
            out.append(item)
        return out

    def list_sessions(self, limit: int = 30) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT s.id, s.created_at, s.candidate_name, s.role, s.mode, s.difficulty,
                       s.status, s.total_questions, s.overall_score,
                       (SELECT COUNT(*) FROM interview_turns t
                        WHERE t.session_id = s.id AND t.answer IS NOT NULL) AS answered_count
                FROM interview_sessions s
                ORDER BY s.id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def count_sessions(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM interview_sessions").fetchone()
            return int(row["cnt"]) if row else 0
