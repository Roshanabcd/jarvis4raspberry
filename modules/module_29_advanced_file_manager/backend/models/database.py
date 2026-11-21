"""Isolated SQLite WAL persistence for JARVIS Module 29 — Advanced File Manager."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FileManagerDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS file_tags (
                    rel_path TEXT PRIMARY KEY,
                    tags_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS trash_items (
                    trash_id TEXT PRIMARY KEY,
                    original_rel_path TEXT NOT NULL,
                    trash_rel_path TEXT NOT NULL,
                    deleted_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def set_tags(self, rel_path: str, tags: List[str]) -> Dict[str, Any]:
        clean = sorted({t.strip().lower() for t in tags if t.strip()})
        now = utc_now_iso()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO file_tags (rel_path, tags_json, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(rel_path) DO UPDATE SET tags_json = excluded.tags_json, updated_at = excluded.updated_at
                """,
                (rel_path, json.dumps(clean), now),
            )
        return {"rel_path": rel_path, "tags": clean, "updated_at": now}

    def get_all_tags(self) -> Dict[str, List[str]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT rel_path, tags_json FROM file_tags").fetchall()
            return {r["rel_path"]: json.loads(r["tags_json"]) for r in rows}

    def add_trash_item(self, trash_id: str, original_rel_path: str, trash_rel_path: str) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO trash_items (trash_id, original_rel_path, trash_rel_path, deleted_at) VALUES (?, ?, ?, ?)",
                (trash_id, original_rel_path, trash_rel_path, now),
            )
        return {"trash_id": trash_id, "original_rel_path": original_rel_path, "trash_rel_path": trash_rel_path, "deleted_at": now}

    def get_trash_item(self, trash_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM trash_items WHERE trash_id = ?", (trash_id,)).fetchone()
            return dict(row) if row else None

    def delete_trash_record(self, trash_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM trash_items WHERE trash_id = ?", (trash_id,))

    def list_trash(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM trash_items ORDER BY deleted_at DESC").fetchall()]

    def add_audit(self, log_id: str, action: str, target_path: str, details: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_logs (log_id, action, target_path, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (log_id, action, target_path, details, utc_now_iso()),
            )

    def list_audits(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]
