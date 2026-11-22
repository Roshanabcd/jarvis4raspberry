"""SQLite WAL persistence layer for JARVIS Module 24 — Email & Calendar Assistant."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EmailCalendarDB:
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
            CREATE TABLE IF NOT EXISTS emails (
                email_id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                priority_score INTEGER NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                archived INTEGER NOT NULL DEFAULT 0,
                received_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS email_drafts (
                draft_id TEXT PRIMARY KEY,
                to_address TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                in_reply_to TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS send_approvals (
                approval_id TEXT PRIMARY KEY,
                draft_id TEXT NOT NULL,
                to_address TEXT NOT NULL,
                subject TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                decided_by TEXT,
                comment TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            );

            CREATE TABLE IF NOT EXISTS calendar_events (
                event_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                location TEXT NOT NULL,
                attendees_json TEXT NOT NULL,
                description TEXT NOT NULL,
                rsvp_status TEXT NOT NULL DEFAULT 'accepted',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # --- Emails ---
    def _row_to_email(self, r: sqlite3.Row) -> Dict[str, Any]:
        d = dict(r)
        d["is_read"] = bool(d["is_read"])
        d["archived"] = bool(d["archived"])
        return d

    def insert_email(self, e: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO emails (email_id, sender, recipient, subject, body, category, priority_score, is_read, archived, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    e["email_id"], e["sender"], e["recipient"], e["subject"], e["body"],
                    e["category"], int(e["priority_score"]), 1 if e.get("is_read") else 0,
                    1 if e.get("archived") else 0, e["received_at"],
                ),
            )
            self._conn.commit()
        return self.get_email(e["email_id"])  # type: ignore[return-value]

    def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM emails WHERE email_id=?", (email_id,)).fetchone()
            return self._row_to_email(r) if r else None

    def list_emails(self, category: Optional[str] = None, include_archived: bool = False) -> List[Dict[str, Any]]:
        with self._lock:
            sql = "SELECT * FROM emails WHERE 1=1"
            params: List[Any] = []
            if not include_archived:
                sql += " AND archived=0"
            if category:
                sql += " AND category=?"
                params.append(category)
            sql += " ORDER BY priority_score DESC, received_at DESC"
            rows = self._conn.execute(sql, tuple(params)).fetchall()
            return [self._row_to_email(r) for r in rows]

    def mark_email(self, email_id: str, *, is_read: Optional[bool] = None, archived: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        cur = self.get_email(email_id)
        if not cur:
            return None
        with self._lock:
            self._conn.execute(
                "UPDATE emails SET is_read=?, archived=? WHERE email_id=?",
                (
                    1 if (cur["is_read"] if is_read is None else is_read) else 0,
                    1 if (cur["archived"] if archived is None else archived) else 0,
                    email_id,
                ),
            )
            self._conn.commit()
        return self.get_email(email_id)

    # --- Drafts & Send Approvals ---
    def create_draft(self, d: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO email_drafts (draft_id, to_address, subject, body, in_reply_to, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (d["draft_id"], d["to_address"], d["subject"], d["body"], d.get("in_reply_to"), d["status"], d["created_at"], d["updated_at"]),
            )
            self._conn.commit()
        return self.get_draft(d["draft_id"])  # type: ignore[return-value]

    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM email_drafts WHERE draft_id=?", (draft_id,)).fetchone()
            return dict(r) if r else None

    def list_drafts(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM email_drafts ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

    def update_draft_status(self, draft_id: str, status: str) -> Optional[Dict[str, Any]]:
        if not self.get_draft(draft_id):
            return None
        with self._lock:
            self._conn.execute("UPDATE email_drafts SET status=?, updated_at=? WHERE draft_id=?", (status, utc_now_iso(), draft_id))
            self._conn.commit()
        return self.get_draft(draft_id)

    def create_approval(self, a: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO send_approvals (approval_id, draft_id, to_address, subject, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (a["approval_id"], a["draft_id"], a["to_address"], a["subject"], a["created_at"]),
            )
            self._conn.commit()
        return self.get_approval(a["approval_id"])  # type: ignore[return-value]

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM send_approvals WHERE approval_id=?", (approval_id,)).fetchone()
            return dict(r) if r else None

    def list_approvals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute("SELECT * FROM send_approvals WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM send_approvals ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def decide_approval(self, approval_id: str, status: str, decided_by: str, comment: str) -> Optional[Dict[str, Any]]:
        if not self.get_approval(approval_id):
            return None
        with self._lock:
            self._conn.execute(
                "UPDATE send_approvals SET status=?, decided_by=?, comment=?, decided_at=? WHERE approval_id=?",
                (status, decided_by, comment, utc_now_iso(), approval_id),
            )
            self._conn.commit()
        return self.get_approval(approval_id)

    # --- Calendar Events ---
    def _row_to_event(self, r: sqlite3.Row) -> Dict[str, Any]:
        d = dict(r)
        d["attendees"] = json.loads(d.pop("attendees_json"))
        return d

    def create_event(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO calendar_events (event_id, title, date, start_time, end_time, location, attendees_json, description, rsvp_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ev["event_id"], ev["title"], ev["date"], ev["start_time"], ev["end_time"],
                    ev["location"], json.dumps(ev["attendees"]), ev["description"],
                    ev["rsvp_status"], ev["created_at"], ev["updated_at"],
                ),
            )
            self._conn.commit()
        return self.get_event(ev["event_id"])  # type: ignore[return-value]

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM calendar_events WHERE event_id=?", (event_id,)).fetchone()
            return self._row_to_event(r) if r else None

    def list_events(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if date:
                rows = self._conn.execute(
                    "SELECT * FROM calendar_events WHERE date=? AND rsvp_status!='cancelled' ORDER BY start_time ASC",
                    (date,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM calendar_events WHERE rsvp_status!='cancelled' ORDER BY date ASC, start_time ASC"
                ).fetchall()
            return [self._row_to_event(r) for r in rows]

    def update_event_rsvp(self, event_id: str, rsvp_status: str) -> Optional[Dict[str, Any]]:
        if not self.get_event(event_id):
            return None
        with self._lock:
            self._conn.execute(
                "UPDATE calendar_events SET rsvp_status=?, updated_at=? WHERE event_id=?",
                (rsvp_status, utc_now_iso(), event_id),
            )
            self._conn.commit()
        return self.get_event(event_id)
