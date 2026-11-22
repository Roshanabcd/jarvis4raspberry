"""SQLite (WAL mode) persistence for domain knowledge base and customer support tickets."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class SupportBotStore:
    """Stores domain KB articles and triaged support tickets in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS kb_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_email TEXT,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    sentiment_score REAL NOT NULL,
                    escalated INTEGER NOT NULL,
                    escalation_team TEXT NOT NULL,
                    escalation_reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reply_text TEXT NOT NULL
                );
                """
            )

    def add_kb_article(self, title: str, category: str, content: str, tags: List[str]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO kb_articles (created_at, title, category, content, tags_json) VALUES (?, ?, ?, ?, ?)",
                (now, title, category, content, json.dumps(tags, ensure_ascii=False)),
            )
            row = conn.execute("SELECT * FROM kb_articles WHERE id = ?", (int(cur.lastrowid),)).fetchone()
        return self._hydrate_kb(row)

    @staticmethod
    def _hydrate_kb(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["tags"] = json.loads(d.pop("tags_json"))
        return d

    def list_kb_articles(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM kb_articles ORDER BY id DESC").fetchall()
        return [self._hydrate_kb(r) for r in rows]

    def create_ticket(
        self,
        customer_name: str,
        customer_email: Optional[str],
        subject: str,
        message: str,
        category: str,
        priority: str,
        sentiment: str,
        sentiment_score: float,
        escalated: bool,
        escalation_team: str,
        escalation_reason: str,
        status: str,
        reply_text: str,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO support_tickets
                    (created_at, customer_name, customer_email, subject, message, category, priority,
                     sentiment, sentiment_score, escalated, escalation_team, escalation_reason, status, reply_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    customer_name,
                    customer_email,
                    subject,
                    message,
                    category,
                    priority,
                    sentiment,
                    sentiment_score,
                    int(escalated),
                    escalation_team,
                    escalation_reason,
                    status,
                    reply_text,
                ),
            )
            row = conn.execute("SELECT * FROM support_tickets WHERE id = ?", (int(cur.lastrowid),)).fetchone()
        return self._hydrate_ticket(row)

    @staticmethod
    def _hydrate_ticket(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["escalated"] = bool(d["escalated"])
        return d

    def list_tickets(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM support_tickets WHERE LOWER(status) = LOWER(?) ORDER BY id DESC LIMIT ?",
                    (status, safe_limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM support_tickets ORDER BY id DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
        return [self._hydrate_ticket(r) for r in rows]

    def update_ticket_status(self, ticket_id: int, status: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.execute("UPDATE support_tickets SET status = ? WHERE id = ?", (status.lower(), ticket_id))
            row = conn.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,)).fetchone()
        return self._hydrate_ticket(row) if row else None

    def counts(self) -> Dict[str, int]:
        with self._connect() as conn:
            kb = int(conn.execute("SELECT COUNT(*) FROM kb_articles").fetchone()[0])
            open_t = int(conn.execute("SELECT COUNT(*) FROM support_tickets WHERE status != 'resolved'").fetchone()[0])
        return {"kb_articles": kb, "open_tickets": open_t}
