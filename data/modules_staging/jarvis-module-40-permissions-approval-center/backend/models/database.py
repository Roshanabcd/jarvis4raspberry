"""SQLite WAL persistence layer for JARVIS Module 40 — Permissions & Approval Center."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ApprovalDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path).expanduser().resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS policies (
                    policy_id TEXT PRIMARY KEY,
                    module_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    description TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(module_id, action)
                );

                CREATE TABLE IF NOT EXISTS approval_requests (
                    request_id TEXT PRIMARY KEY,
                    requester TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reviewer TEXT,
                    rationale TEXT,
                    expires_at_epoch REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT
                );

                CREATE TABLE IF NOT EXISTS approval_audit (
                    event_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _row_to_request(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "request_id": row["request_id"],
            "requester": row["requester"],
            "module_id": row["module_id"],
            "action": row["action"],
            "risk_level": row["risk_level"],
            "summary": row["summary"],
            "payload": json.loads(row["payload_json"]),
            "status": row["status"],
            "reviewer": row["reviewer"],
            "rationale": row["rationale"],
            "expires_at_epoch": row["expires_at_epoch"],
            "created_at": row["created_at"],
            "decided_at": row["decided_at"],
        }

    def upsert_policy(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO policies (policy_id, module_id, action, risk_level, mode, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(module_id, action) DO UPDATE SET
                    risk_level = excluded.risk_level,
                    mode = excluded.mode,
                    description = excluded.description,
                    updated_at = excluded.updated_at
                """,
                (
                    item["policy_id"],
                    item["module_id"],
                    item["action"],
                    item["risk_level"],
                    item["mode"],
                    item["description"],
                    item["updated_at"],
                ),
            )
            row = conn.execute(
                "SELECT * FROM policies WHERE module_id = ? AND action = ?",
                (item["module_id"], item["action"]),
            ).fetchone()
        return dict(row)

    def get_policy(self, module_id: str, action: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM policies WHERE module_id = ? AND action = ?", (module_id, action)
            ).fetchone()
        return dict(row) if row else None

    def list_policies(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM policies ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

    def add_request(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO approval_requests (
                    request_id, requester, module_id, action, risk_level, summary,
                    payload_json, status, reviewer, rationale, expires_at_epoch, created_at, decided_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["request_id"],
                    item["requester"],
                    item["module_id"],
                    item["action"],
                    item["risk_level"],
                    item["summary"],
                    json.dumps(item["payload"]),
                    item["status"],
                    item["reviewer"],
                    item["rationale"],
                    item["expires_at_epoch"],
                    item["created_at"],
                    item["decided_at"],
                ),
            )
        return item

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM approval_requests WHERE request_id = ?", (request_id,)).fetchone()
        return self._row_to_request(row) if row else None

    def update_request_decision(
        self, request_id: str, status: str, reviewer: Optional[str], rationale: str, decided_at: str
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE approval_requests
                SET status = ?, reviewer = ?, rationale = ?, decided_at = ?
                WHERE request_id = ?
                """,
                (status, reviewer, rationale, decided_at, request_id),
            )
        return self.get_request(request_id)  # type: ignore[return-value]

    def list_requests(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM approval_requests WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM approval_requests ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
        return [self._row_to_request(r) for r in rows]

    def add_audit(self, event: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO approval_audit (event_id, request_id, actor, event_type, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["request_id"],
                    event["actor"],
                    event["event_type"],
                    event["details"],
                    event["created_at"],
                ),
            )
        return event

    def list_audit(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM approval_audit ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
