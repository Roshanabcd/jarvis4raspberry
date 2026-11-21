"""SQLite WAL persistence layer for JARVIS Module 41 — Universal Notification Center."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class NotificationDB:
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
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id TEXT PRIMARY KEY,
                    source_module TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    channels_json TEXT NOT NULL,
                    delivered_channels_json TEXT NOT NULL,
                    dedupe_key TEXT UNIQUE,
                    metadata_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS preferences (
                    pref_id INTEGER PRIMARY KEY CHECK (pref_id = 1),
                    dnd_enabled INTEGER NOT NULL,
                    allow_critical_during_dnd INTEGER NOT NULL,
                    enabled_channels_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            row = conn.execute("SELECT * FROM preferences WHERE pref_id = 1").fetchone()
            if not row:
                conn.execute(
                    """
                    INSERT INTO preferences (pref_id, dnd_enabled, allow_critical_during_dnd, enabled_channels_json, updated_at)
                    VALUES (1, 0, 1, ?, ?)
                    """,
                    (json.dumps(["hud", "desktop", "voice"]), utc_now_iso()),
                )

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "notification_id": row["notification_id"],
            "source_module": row["source_module"],
            "title": row["title"],
            "message": row["message"],
            "priority": row["priority"],
            "channels": json.loads(row["channels_json"]),
            "delivered_channels": json.loads(row["delivered_channels_json"]),
            "dedupe_key": row["dedupe_key"],
            "metadata": json.loads(row["metadata_json"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def get_preferences(self) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM preferences WHERE pref_id = 1").fetchone()
        return {
            "dnd_enabled": bool(row["dnd_enabled"]),
            "allow_critical_during_dnd": bool(row["allow_critical_during_dnd"]),
            "enabled_channels": json.loads(row["enabled_channels_json"]),
            "updated_at": row["updated_at"],
        }

    def update_preferences(
        self, dnd_enabled: bool, allow_critical_during_dnd: bool, enabled_channels: List[str], now: str
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE preferences
                SET dnd_enabled = ?, allow_critical_during_dnd = ?, enabled_channels_json = ?, updated_at = ?
                WHERE pref_id = 1
                """,
                (1 if dnd_enabled else 0, 1 if allow_critical_during_dnd else 0, json.dumps(enabled_channels), now),
            )
        return self.get_preferences()

    def get_by_dedupe_key(self, dedupe_key: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM notifications WHERE dedupe_key = ?", (dedupe_key,)).fetchone()
        return self._row_to_item(row) if row else None

    def add_notification(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO notifications (
                    notification_id, source_module, title, message, priority,
                    channels_json, delivered_channels_json, dedupe_key, metadata_json,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["notification_id"],
                    item["source_module"],
                    item["title"],
                    item["message"],
                    item["priority"],
                    json.dumps(item["channels"]),
                    json.dumps(item["delivered_channels"]),
                    item["dedupe_key"],
                    json.dumps(item["metadata"]),
                    item["status"],
                    item["created_at"],
                    item["updated_at"],
                ),
            )
        return item

    def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM notifications WHERE notification_id = ?", (notification_id,)).fetchone()
        return self._row_to_item(row) if row else None

    def update_status(self, notification_id: str, status: str, now: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.execute(
                "UPDATE notifications SET status = ?, updated_at = ? WHERE notification_id = ?",
                (status, now, notification_id),
            )
        return self.get_notification(notification_id)

    def list_notifications(
        self, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if priority:
            clauses.append("priority = ?")
            params.append(priority)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM notifications {where} ORDER BY created_at DESC LIMIT ?",
                tuple(params),
            ).fetchall()
        return [self._row_to_item(r) for r in rows]
