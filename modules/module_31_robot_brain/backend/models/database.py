"""SQLite WAL persistence layer for JARVIS Module 31 — JARVIS Robot Brain."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RobotBrainDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS robot_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    mode TEXT NOT NULL,
                    estop_engaged INTEGER NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    heading_deg REAL NOT NULL,
                    linear_mps REAL NOT NULL,
                    angular_rps REAL NOT NULL,
                    battery_pct REAL NOT NULL,
                    front_obstacle_m REAL NOT NULL,
                    cpu_temp_c REAL NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS waypoints (
                    waypoint_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    zone TEXT NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            row = conn.execute("SELECT id FROM robot_state WHERE id = 1").fetchone()
            if not row:
                conn.execute(
                    """
                    INSERT INTO robot_state
                    (id, mode, estop_engaged, x, y, heading_deg, linear_mps, angular_rps, battery_pct, front_obstacle_m, cpu_temp_c, updated_at)
                    VALUES (1, 'idle', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 92.0, 2.5, 44.0, ?)
                    """,
                    (utc_now_iso(),),
                )

    def get_state(self) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM robot_state WHERE id = 1").fetchone()
            d = dict(row)
            d["estop_engaged"] = bool(d["estop_engaged"])
            return d

    def update_state(self, **fields: Any) -> Dict[str, Any]:
        current = self.get_state()
        current.update(fields)
        current["updated_at"] = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE robot_state
                SET mode = ?, estop_engaged = ?, x = ?, y = ?, heading_deg = ?,
                    linear_mps = ?, angular_rps = ?, battery_pct = ?,
                    front_obstacle_m = ?, cpu_temp_c = ?, updated_at = ?
                WHERE id = 1
                """,
                (
                    current["mode"],
                    1 if current["estop_engaged"] else 0,
                    float(current["x"]),
                    float(current["y"]),
                    float(current["heading_deg"]),
                    float(current["linear_mps"]),
                    float(current["angular_rps"]),
                    float(current["battery_pct"]),
                    float(current["front_obstacle_m"]),
                    float(current["cpu_temp_c"]),
                    current["updated_at"],
                ),
            )
        return self.get_state()

    def create_waypoint(self, wp: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO waypoints (waypoint_id, name, zone, x, y, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (wp["waypoint_id"], wp["name"], wp["zone"], wp["x"], wp["y"], wp["created_at"]),
            )
        return wp

    def get_waypoint(self, waypoint_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM waypoints WHERE waypoint_id = ?", (waypoint_id,)).fetchone()
            return dict(row) if row else None

    def list_waypoints(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM waypoints ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def create_mission(self, m: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO missions (mission_id, name, status, steps_json, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    m["mission_id"],
                    m["name"],
                    m["status"],
                    json.dumps(m["steps"]),
                    json.dumps(m["result"]),
                    m["created_at"],
                    m["updated_at"],
                ),
            )
        return m

    def _mission_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "mission_id": row["mission_id"],
            "name": row["name"],
            "status": row["status"],
            "steps": json.loads(row["steps_json"]),
            "result": json.loads(row["result_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM missions WHERE mission_id = ?", (mission_id,)).fetchone()
            return self._mission_row(row) if row else None

    def update_mission(self, mission_id: str, status: str, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "UPDATE missions SET status = ?, result_json = ?, updated_at = ? WHERE mission_id = ?",
                (status, json.dumps(result), now, mission_id),
            )
        return self.get_mission(mission_id)

    def list_missions(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM missions ORDER BY created_at DESC").fetchall()
            return [self._mission_row(r) for r in rows]

    def add_event(self, event_id: str, event_type: str, detail: str) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO telemetry_events (event_id, event_type, detail, created_at) VALUES (?, ?, ?, ?)",
                (event_id, event_type, detail, now),
            )
        return {"event_id": event_id, "event_type": event_type, "detail": detail, "created_at": now}

    def list_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM telemetry_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]
