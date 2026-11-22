"""SQLite WAL persistence layer for JARVIS Module 23 — Personal Executive Assistant."""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutiveAssistantDB:
    def __init__(self, db_path: str) -> None:
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA foreign_keys=ON;")
            self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS goals (
                goal_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                horizon TEXT NOT NULL,
                priority TEXT NOT NULL,
                target_date TEXT,
                progress_pct INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                urgent INTEGER NOT NULL DEFAULT 0,
                important INTEGER NOT NULL DEFAULT 1,
                quadrant TEXT NOT NULL,
                due_date TEXT,
                estimated_minutes INTEGER NOT NULL DEFAULT 45,
                goal_id TEXT,
                status TEXT NOT NULL DEFAULT 'todo',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS time_blocks (
                block_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                title TEXT NOT NULL,
                block_type TEXT NOT NULL,
                task_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS habits (
                habit_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                cadence TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS habit_checkins (
                habit_id TEXT NOT NULL,
                checkin_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (habit_id, checkin_date),
                FOREIGN KEY (habit_id) REFERENCES habits(habit_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS follow_ups (
                followup_id TEXT PRIMARY KEY,
                person TEXT NOT NULL,
                topic TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # --- Goals ---
    def create_goal(self, g: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO goals (goal_id, title, horizon, priority, target_date, progress_pct, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (g["goal_id"], g["title"], g["horizon"], g["priority"], g.get("target_date"), g["progress_pct"], g["status"], g["created_at"], g["updated_at"]),
            )
            self._conn.commit()
        return self.get_goal(g["goal_id"])  # type: ignore[return-value]

    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
            return dict(r) if r else None

    def list_goals(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM goals ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def update_goal(self, goal_id: str, progress_pct: int, status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        cur = self.get_goal(goal_id)
        if not cur:
            return None
        new_status = status or ("completed" if progress_pct >= 100 else cur["status"])
        with self._lock:
            self._conn.execute(
                "UPDATE goals SET progress_pct=?, status=?, updated_at=? WHERE goal_id=?",
                (progress_pct, new_status, utc_now_iso(), goal_id),
            )
            self._conn.commit()
        return self.get_goal(goal_id)

    # --- Tasks ---
    def _row_to_task(self, r: sqlite3.Row) -> Dict[str, Any]:
        d = dict(r)
        d["urgent"] = bool(d["urgent"])
        d["important"] = bool(d["important"])
        return d

    def create_task(self, t: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO tasks (task_id, title, description, priority, urgent, important, quadrant, due_date, estimated_minutes, goal_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t["task_id"], t["title"], t["description"], t["priority"],
                    1 if t["urgent"] else 0, 1 if t["important"] else 0, t["quadrant"],
                    t.get("due_date"), t["estimated_minutes"], t.get("goal_id"),
                    t["status"], t["created_at"], t["updated_at"],
                ),
            )
            self._conn.commit()
        return self.get_task(t["task_id"])  # type: ignore[return-value]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            return self._row_to_task(r) if r else None

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute("SELECT * FROM tasks WHERE status=? ORDER BY priority ASC, created_at ASC", (status,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM tasks ORDER BY priority ASC, created_at ASC").fetchall()
            return [self._row_to_task(r) for r in rows]

    def update_task_status(self, task_id: str, status: str) -> Optional[Dict[str, Any]]:
        if not self.get_task(task_id):
            return None
        with self._lock:
            self._conn.execute("UPDATE tasks SET status=?, updated_at=? WHERE task_id=?", (status, utc_now_iso(), task_id))
            self._conn.commit()
        return self.get_task(task_id)

    # --- Time Blocks ---
    def create_time_block(self, b: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO time_blocks (block_id, date, start_time, end_time, title, block_type, task_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (b["block_id"], b["date"], b["start_time"], b["end_time"], b["title"], b["block_type"], b.get("task_id"), b["created_at"]),
            )
            self._conn.commit()
        return b

    def list_time_blocks(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if date:
                rows = self._conn.execute("SELECT * FROM time_blocks WHERE date=? ORDER BY start_time ASC", (date,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM time_blocks ORDER BY date DESC, start_time ASC").fetchall()
            return [dict(r) for r in rows]

    # --- Habits ---
    def create_habit(self, h: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                "INSERT INTO habits (habit_id, name, cadence, created_at) VALUES (?, ?, ?, ?)",
                (h["habit_id"], h["name"], h["cadence"], h["created_at"]),
            )
            self._conn.commit()
        return h

    def list_habits(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM habits ORDER BY created_at ASC").fetchall()
            out = []
            for r in rows:
                h = dict(r)
                dates = [
                    c["checkin_date"]
                    for c in self._conn.execute(
                        "SELECT checkin_date FROM habit_checkins WHERE habit_id=? ORDER BY checkin_date DESC",
                        (h["habit_id"],),
                    ).fetchall()
                ]
                h["checkin_dates"] = dates
                h["total_checkins"] = len(dates)
                out.append(h)
            return out

    def record_habit_checkin(self, habit_id: str, checkin_date: str) -> bool:
        with self._lock:
            exists = self._conn.execute("SELECT 1 FROM habits WHERE habit_id=?", (habit_id,)).fetchone()
            if not exists:
                return False
            self._conn.execute(
                "INSERT OR IGNORE INTO habit_checkins (habit_id, checkin_date, created_at) VALUES (?, ?, ?)",
                (habit_id, checkin_date, utc_now_iso()),
            )
            self._conn.commit()
            return True

    # --- Follow-ups ---
    def create_followup(self, f: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO follow_ups (followup_id, person, topic, due_date, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (f["followup_id"], f["person"], f["topic"], f["due_date"], f["status"], f["created_at"], f["updated_at"]),
            )
            self._conn.commit()
        return f

    def list_followups(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute("SELECT * FROM follow_ups WHERE status=? ORDER BY due_date ASC", (status,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM follow_ups ORDER BY due_date ASC").fetchall()
            return [dict(r) for r in rows]

    def update_followup(self, followup_id: str, status: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM follow_ups WHERE followup_id=?", (followup_id,)).fetchone()
            if not cur:
                return None
            self._conn.execute("UPDATE follow_ups SET status=?, updated_at=? WHERE followup_id=?", (status, utc_now_iso(), followup_id))
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM follow_ups WHERE followup_id=?", (followup_id,)).fetchone()
            return dict(row) if row else None
