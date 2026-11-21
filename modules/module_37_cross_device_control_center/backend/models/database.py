"""SQLite WAL persistence layer for JARVIS Module 37 — Cross-Device Control Center."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class DeviceMeshDB:
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
                CREATE TABLE IF NOT EXISTS device_nodes (
                    device_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    battery_pct INTEGER NOT NULL,
                    online INTEGER NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS device_commands (
                    command_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    action TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    simulated INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (device_id) REFERENCES device_nodes(device_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS clipboard_entries (
                    entry_id TEXT PRIMARY KEY,
                    source_device_id TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_device_id) REFERENCES device_nodes(device_id) ON DELETE CASCADE
                );
                """
            )

    @staticmethod
    def _row_to_device(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "device_id": row["device_id"],
            "name": row["name"],
            "device_type": row["device_type"],
            "platform": row["platform"],
            "capabilities": json.loads(row["capabilities_json"]),
            "battery_pct": row["battery_pct"],
            "online": bool(row["online"]),
            "last_seen_at": row["last_seen_at"],
            "created_at": row["created_at"],
        }

    def add_device(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO device_nodes (
                    device_id, name, device_type, platform, capabilities_json,
                    battery_pct, online, last_seen_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["device_id"],
                    item["name"],
                    item["device_type"],
                    item["platform"],
                    json.dumps(item["capabilities"]),
                    item["battery_pct"],
                    1 if item["online"] else 0,
                    item["last_seen_at"],
                    item["created_at"],
                ),
            )
        return item

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM device_nodes WHERE device_id = ?", (device_id,)).fetchone()
        return self._row_to_device(row) if row else None

    def list_devices(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM device_nodes ORDER BY created_at DESC").fetchall()
        return [self._row_to_device(r) for r in rows]

    def update_device_heartbeat(
        self, device_id: str, online: bool, battery_pct: Optional[int], last_seen_at: str
    ) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            if battery_pct is not None:
                conn.execute(
                    "UPDATE device_nodes SET online = ?, battery_pct = ?, last_seen_at = ? WHERE device_id = ?",
                    (1 if online else 0, battery_pct, last_seen_at, device_id),
                )
            else:
                conn.execute(
                    "UPDATE device_nodes SET online = ?, last_seen_at = ? WHERE device_id = ?",
                    (1 if online else 0, last_seen_at, device_id),
                )
        return self.get_device(device_id)

    def add_command(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO device_commands (
                    command_id, device_id, capability, action, params_json,
                    status, result_json, simulated, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["command_id"],
                    item["device_id"],
                    item["capability"],
                    item["action"],
                    json.dumps(item["params"]),
                    item["status"],
                    json.dumps(item["result"]),
                    1 if item["simulated"] else 0,
                    item["created_at"],
                ),
            )
        return item

    def list_commands(self, device_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if device_id:
                rows = conn.execute(
                    "SELECT * FROM device_commands WHERE device_id = ? ORDER BY created_at DESC LIMIT ?",
                    (device_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM device_commands ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
        return [
            {
                "command_id": r["command_id"],
                "device_id": r["device_id"],
                "capability": r["capability"],
                "action": r["action"],
                "params": json.loads(r["params_json"]),
                "status": r["status"],
                "result": json.loads(r["result_json"]),
                "simulated": bool(r["simulated"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def add_clipboard(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO clipboard_entries (
                    entry_id, source_device_id, mime_type, content, sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item["entry_id"],
                    item["source_device_id"],
                    item["mime_type"],
                    item["content"],
                    item["sha256"],
                    item["created_at"],
                ),
            )
        return item

    def list_clipboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM clipboard_entries ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            {
                "entry_id": r["entry_id"],
                "source_device_id": r["source_device_id"],
                "mime_type": r["mime_type"],
                "content": r["content"],
                "sha256": r["sha256"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
