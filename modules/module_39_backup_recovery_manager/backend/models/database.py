"""SQLite WAL persistence layer for JARVIS Module 39 — Backup & Recovery Manager."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class BackupDB:
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
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_rel_path TEXT NOT NULL,
                    archive_filename TEXT NOT NULL,
                    file_count INTEGER NOT NULL,
                    byte_size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS restore_runs (
                    restore_id TEXT PRIMARY KEY,
                    snapshot_id TEXT NOT NULL,
                    target_rel_path TEXT NOT NULL,
                    restored_files INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
                );
                """
            )

    def add_snapshot(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO snapshots (
                    snapshot_id, name, source_rel_path, archive_filename,
                    file_count, byte_size, sha256, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["snapshot_id"],
                    item["name"],
                    item["source_rel_path"],
                    item["archive_filename"],
                    item["file_count"],
                    item["byte_size"],
                    item["sha256"],
                    item["notes"],
                    item["created_at"],
                ),
            )
        return item

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
        return dict(row) if row else None

    def list_snapshots(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM snapshots ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def add_restore_run(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO restore_runs (
                    restore_id, snapshot_id, target_rel_path, restored_files, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item["restore_id"],
                    item["snapshot_id"],
                    item["target_rel_path"],
                    item["restored_files"],
                    item["status"],
                    item["created_at"],
                ),
            )
        return item

    def list_restores(self, snapshot_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if snapshot_id:
                rows = conn.execute(
                    "SELECT * FROM restore_runs WHERE snapshot_id = ? ORDER BY created_at DESC LIMIT ?",
                    (snapshot_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM restore_runs ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
        return [dict(r) for r in rows]
