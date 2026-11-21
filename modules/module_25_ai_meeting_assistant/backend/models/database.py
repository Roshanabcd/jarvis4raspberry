"""SQLite WAL persistence layer for JARVIS Module 25 — AI Meeting Assistant."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MeetingAssistantDB:
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
            CREATE TABLE IF NOT EXISTS meetings (
                meeting_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                meeting_date TEXT NOT NULL,
                participants_json TEXT NOT NULL,
                agenda TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'live',
                summary_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transcript_segments (
                segment_id TEXT PRIMARY KEY,
                meeting_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp_sec INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS action_items (
                item_id TEXT PRIMARY KEY,
                meeting_id TEXT NOT NULL,
                owner TEXT NOT NULL,
                description TEXT NOT NULL,
                due_hint TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _row_to_meeting(self, r: sqlite3.Row) -> Dict[str, Any]:
        d = dict(r)
        d["participants"] = json.loads(d.pop("participants_json"))
        raw_sum = d.pop("summary_json")
        d["summary"] = json.loads(raw_sum) if raw_sum else None
        return d

    def create_meeting(self, m: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO meetings (meeting_id, title, meeting_date, participants_json, agenda, status, summary_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (m["meeting_id"], m["title"], m["meeting_date"], json.dumps(m["participants"]), m["agenda"], m["status"], m["created_at"], m["updated_at"]),
            )
            self._conn.commit()
        return self.get_meeting(m["meeting_id"])  # type: ignore[return-value]

    def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM meetings WHERE meeting_id=?", (meeting_id,)).fetchone()
            return self._row_to_meeting(r) if r else None

    def list_meetings(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM meetings ORDER BY created_at DESC").fetchall()
            return [self._row_to_meeting(r) for r in rows]

    def save_meeting_summary(self, meeting_id: str, summary: Dict[str, Any], status: str = "completed") -> Optional[Dict[str, Any]]:
        if not self.get_meeting(meeting_id):
            return None
        with self._lock:
            self._conn.execute(
                "UPDATE meetings SET summary_json=?, status=?, updated_at=? WHERE meeting_id=?",
                (json.dumps(summary), status, utc_now_iso(), meeting_id),
            )
            self._conn.commit()
        return self.get_meeting(meeting_id)

    # --- Transcript Segments ---
    def add_segment(self, seg: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO transcript_segments (segment_id, meeting_id, speaker, text, timestamp_sec, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (seg["segment_id"], seg["meeting_id"], seg["speaker"], seg["text"], int(seg["timestamp_sec"]), seg["created_at"]),
            )
            self._conn.commit()
        return seg

    def list_segments(self, meeting_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM transcript_segments WHERE meeting_id=? ORDER BY timestamp_sec ASC, created_at ASC",
                (meeting_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def search_transcripts(self, query: str, limit: int = 40) -> List[Dict[str, Any]]:
        pattern = f"%{query.strip()}%"
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT s.*, m.title AS meeting_title, m.meeting_date
                FROM transcript_segments s
                JOIN meetings m ON m.meeting_id = s.meeting_id
                WHERE s.text LIKE ? OR s.speaker LIKE ?
                ORDER BY s.created_at DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Action Items ---
    def replace_action_items(self, meeting_id: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        with self._lock:
            self._conn.execute("DELETE FROM action_items WHERE meeting_id=?", (meeting_id,))
            for it in items:
                self._conn.execute(
                    """
                    INSERT INTO action_items (item_id, meeting_id, owner, description, due_hint, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (it["item_id"], meeting_id, it["owner"], it["description"], it.get("due_hint"), it["status"], it["created_at"], it["updated_at"]),
                )
            self._conn.commit()
        return self.list_action_items(meeting_id=meeting_id)

    def list_action_items(self, meeting_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            sql = "SELECT * FROM action_items WHERE 1=1"
            params: List[Any] = []
            if meeting_id:
                sql += " AND meeting_id=?"
                params.append(meeting_id)
            if status:
                sql += " AND status=?"
                params.append(status)
            sql += " ORDER BY created_at ASC"
            rows = self._conn.execute(sql, tuple(params)).fetchall()
            return [dict(r) for r in rows]

    def update_action_item(self, item_id: str, status: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM action_items WHERE item_id=?", (item_id,)).fetchone()
            if not cur:
                return None
            self._conn.execute("UPDATE action_items SET status=?, updated_at=? WHERE item_id=?", (status, utc_now_iso(), item_id))
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM action_items WHERE item_id=?", (item_id,)).fetchone()
            return dict(row) if row else None
