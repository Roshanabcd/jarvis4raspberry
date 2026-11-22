"""SQLite WAL persistence for sessions, conversation turns, and context."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationalDB:
    def __init__(self, db_path: str = "./data/jarvis_conversational_ai.db") -> None:
        self.db_path = db_path
        self._lock = threading.RLock()
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA foreign_keys=ON;")
            self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                persona TEXT NOT NULL DEFAULT 'aria',
                system_prompt TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                persona TEXT NOT NULL DEFAULT 'aria',
                provider TEXT NOT NULL DEFAULT 'simulated_local',
                fallback_used INTEGER NOT NULL DEFAULT 0,
                interrupted INTEGER NOT NULL DEFAULT 0,
                facial_state TEXT NOT NULL DEFAULT 'idle',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at ASC);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def create_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO sessions (session_id, title, persona, system_prompt, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["session_id"],
                    session["title"],
                    session["persona"],
                    session.get("system_prompt", ""),
                    session["created_at"],
                    session["updated_at"],
                ),
            )
            self._conn.commit()
            return self.get_session(session["session_id"])  # type: ignore[return-value]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            return dict(row) if row else None

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            self._conn.commit()
            return cur.rowcount > 0

    def add_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        now = msg.get("created_at") or utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO messages (
                    message_id, session_id, role, content, persona, provider,
                    fallback_used, interrupted, facial_state, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg["message_id"],
                    msg["session_id"],
                    msg["role"],
                    msg["content"],
                    msg.get("persona", "aria"),
                    msg.get("provider", "simulated_local"),
                    1 if msg.get("fallback_used") else 0,
                    1 if msg.get("interrupted") else 0,
                    msg.get("facial_state", "idle"),
                    json.dumps(msg.get("metadata", {})),
                    now,
                ),
            )
            self._conn.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, msg["session_id"]))
            self._conn.commit()
            return {**msg, "created_at": now}

    def list_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
                (session_id, limit),
            ).fetchall()
            return [
                {
                    "message_id": r["message_id"],
                    "session_id": r["session_id"],
                    "role": r["role"],
                    "content": r["content"],
                    "persona": r["persona"],
                    "provider": r["provider"],
                    "fallback_used": bool(r["fallback_used"]),
                    "interrupted": bool(r["interrupted"]),
                    "facial_state": r["facial_state"],
                    "metadata": json.loads(r["metadata_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def clear_session_messages(self, session_id: str) -> int:
        with self._lock:
            cur = self._conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            self._conn.commit()
            return cur.rowcount
