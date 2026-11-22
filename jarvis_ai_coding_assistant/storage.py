"""SQLite (WAL mode) persistence and audit logging for AI Coding Assistant."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class CodingAssistantStore:
    """Lightweight SQLite WAL store for coding sessions and audit trails."""

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
                CREATE TABLE IF NOT EXISTS coding_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    action TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    file_path TEXT,
                    summary TEXT NOT NULL,
                    score INTEGER,
                    payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workspace_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    session_id INTEGER,
                    file_path TEXT NOT NULL,
                    dry_run INTEGER NOT NULL,
                    backup_path TEXT,
                    bytes_written INTEGER NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES coding_sessions(id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_coding_sessions_created
                    ON coding_sessions(created_at DESC);
                """
            )

    def record_session(
        self,
        action: str,
        provider: str,
        summary: str,
        payload: Dict[str, Any],
        file_path: Optional[str] = None,
        score: Optional[int] = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO coding_sessions
                    (created_at, action, provider, file_path, summary, score, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    action,
                    provider,
                    file_path,
                    summary[:500],
                    score,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def record_workspace_audit(
        self,
        file_path: str,
        dry_run: bool,
        bytes_written: int,
        backup_path: Optional[str] = None,
        session_id: Optional[int] = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO workspace_audit
                    (created_at, session_id, file_path, dry_run, backup_path, bytes_written)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, session_id, file_path, int(dry_run), backup_path, bytes_written),
            )
            return int(cursor.lastrowid)

    def list_history(self, limit: int = 30) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, action, provider, file_path, summary, score
                FROM coding_sessions
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def count_sessions(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM coding_sessions").fetchone()
            return int(row["cnt"]) if row else 0
