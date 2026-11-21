"""Isolated SQLite WAL persistence for JARVIS Module 30 — Smart Home Controller."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SmartHomeDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    room TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    rated_watts REAL NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS scenes (
                    scene_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    actions_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sensor_device_id TEXT NOT NULL,
                    metric_key TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    target_device_id TEXT NOT NULL,
                    target_command TEXT NOT NULL,
                    target_value_json TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS device_events (
                    event_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def _row_device(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "device_id": r["device_id"],
            "name": r["name"],
            "room": r["room"],
            "device_type": r["device_type"],
            "rated_watts": r["rated_watts"],
            "state": json.loads(r["state_json"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }

    def create_device(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO devices (device_id, name, room, device_type, rated_watts, state_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["device_id"],
                    rec["name"],
                    rec["room"],
                    rec["device_type"],
                    rec["rated_watts"],
                    json.dumps(rec["state"]),
                    rec["created_at"],
                    rec["updated_at"],
                ),
            )
        return self.get_device(rec["device_id"])  # type: ignore[return-value]

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,)).fetchone()
            return self._row_device(row) if row else None

    def list_devices(self, room: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if room:
                rows = conn.execute("SELECT * FROM devices WHERE LOWER(room) = LOWER(?) ORDER BY name ASC", (room,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM devices ORDER BY room ASC, name ASC").fetchall()
            return [self._row_device(r) for r in rows]

    def update_device_state(self, device_id: str, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE devices SET state_json = ?, updated_at = ? WHERE device_id = ?", (json.dumps(state), utc_now_iso(), device_id))
        return self.get_device(device_id)

    def create_scene(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO scenes (scene_id, name, description, actions_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (rec["scene_id"], rec["name"], rec["description"], json.dumps(rec["actions"]), rec["created_at"]),
            )
        return self.get_scene(rec["scene_id"])  # type: ignore[return-value]

    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            r = conn.execute("SELECT * FROM scenes WHERE scene_id = ?", (scene_id,)).fetchone()
            if not r:
                return None
            return {
                "scene_id": r["scene_id"],
                "name": r["name"],
                "description": r["description"],
                "actions": json.loads(r["actions_json"]),
                "created_at": r["created_at"],
            }

    def list_scenes(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM scenes ORDER BY created_at DESC").fetchall()
            return [
                {
                    "scene_id": r["scene_id"],
                    "name": r["name"],
                    "description": r["description"],
                    "actions": json.loads(r["actions_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def create_rule(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rules (
                    rule_id, name, sensor_device_id, metric_key, operator, threshold,
                    target_device_id, target_command, target_value_json, enabled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["rule_id"],
                    rec["name"],
                    rec["sensor_device_id"],
                    rec["metric_key"],
                    rec["operator"],
                    rec["threshold"],
                    rec["target_device_id"],
                    rec["target_command"],
                    json.dumps(rec.get("target_value")),
                    1,
                    rec["created_at"],
                ),
            )
        return rec

    def list_rules(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM rules WHERE enabled = 1 ORDER BY created_at DESC").fetchall()
            return [
                {
                    "rule_id": r["rule_id"],
                    "name": r["name"],
                    "sensor_device_id": r["sensor_device_id"],
                    "metric_key": r["metric_key"],
                    "operator": r["operator"],
                    "threshold": r["threshold"],
                    "target_device_id": r["target_device_id"],
                    "target_command": r["target_command"],
                    "target_value": json.loads(r["target_value_json"]) if r["target_value_json"] is not None else None,
                    "enabled": bool(r["enabled"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def add_event(self, event_id: str, device_id: str, action: str, details: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO device_events (event_id, device_id, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (event_id, device_id, action, details, utc_now_iso()),
            )

    def list_events(self, limit: int = 40) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM device_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]
