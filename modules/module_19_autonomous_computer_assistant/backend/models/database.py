"""SQLite WAL persistence layer for JARVIS Module 19."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ComputerAssistantDB:
    """Thread-safe SQLite WAL store for action history, approvals, screenshots, and safety state."""

    def __init__(self, db_path: str = "./data/jarvis_computer_assistant.db") -> None:
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
            CREATE TABLE IF NOT EXISTS actions (
                action_id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT NOT NULL,
                dry_run INTEGER NOT NULL DEFAULT 0,
                simulated INTEGER NOT NULL DEFAULT 1,
                requested_by TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                params_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT,
                error TEXT,
                replayed_from TEXT,
                duration_ms REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approval_requests (
                approval_id TEXT PRIMARY KEY,
                action_id TEXT NOT NULL UNIQUE,
                action_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                decided_by TEXT,
                comment TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                FOREIGN KEY (action_id) REFERENCES actions(action_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS screenshots (
                screenshot_id TEXT PRIMARY KEY,
                action_id TEXT,
                window_id TEXT,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                simulated INTEGER NOT NULL DEFAULT 1,
                image_b64 TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS diagnostic_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id TEXT,
                level TEXT NOT NULL DEFAULT 'INFO',
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS safety_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_actions_created ON actions(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_approvals_status ON approval_requests(status);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # --- Safety State / Policy ---
    def get_state(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._lock:
            row = self._conn.execute("SELECT value FROM safety_state WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_state(self, key: str, value: str) -> None:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO safety_state(key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, now),
            )
            self._conn.commit()

    # --- Actions ---
    def create_action(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO actions (
                    action_id, action_type, risk_level, status, dry_run, simulated,
                    requested_by, reason, params_json, result_json, error, replayed_from,
                    duration_ms, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["action_id"],
                    rec["action_type"],
                    rec["risk_level"],
                    rec["status"],
                    1 if rec.get("dry_run") else 0,
                    1 if rec.get("simulated", True) else 0,
                    rec["requested_by"],
                    rec.get("reason", ""),
                    json.dumps(rec.get("params", {})),
                    json.dumps(rec["result"]) if rec.get("result") is not None else None,
                    rec.get("error"),
                    rec.get("replayed_from"),
                    float(rec.get("duration_ms", 0.0)),
                    rec["created_at"],
                    rec["updated_at"],
                ),
            )
            self._conn.commit()
            return self.get_action(rec["action_id"])  # type: ignore[return-value]

    def _row_to_action(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "action_id": row["action_id"],
            "action_type": row["action_type"],
            "risk_level": row["risk_level"],
            "status": row["status"],
            "dry_run": bool(row["dry_run"]),
            "simulated": bool(row["simulated"]),
            "requested_by": row["requested_by"],
            "reason": row["reason"],
            "params": json.loads(row["params_json"]),
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
            "error": row["error"],
            "replayed_from": row["replayed_from"],
            "duration_ms": row["duration_ms"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)).fetchone()
            return self._row_to_action(row) if row else None

    def list_actions(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM actions WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit)
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM actions ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [self._row_to_action(r) for r in rows]

    def update_action(self, action_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        for k, v in fields.items():
            if k == "result":
                payload["result_json"] = json.dumps(v) if v is not None else None
            elif k in ("status", "error", "duration_ms"):
                payload[k] = v
        payload["updated_at"] = utc_now_iso()
        cols = ", ".join(f"{k} = ?" for k in payload)
        with self._lock:
            self._conn.execute(f"UPDATE actions SET {cols} WHERE action_id = ?", list(payload.values()) + [action_id])
            self._conn.commit()
            return self.get_action(action_id)

    # --- Approvals ---
    def create_approval(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO approval_requests (
                    approval_id, action_id, action_type, risk_level, prompt, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["approval_id"],
                    rec["action_id"],
                    rec["action_type"],
                    rec["risk_level"],
                    rec["prompt"],
                    rec.get("status", "pending"),
                    rec["created_at"],
                ),
            )
            self._conn.commit()
            return self.get_approval(rec["approval_id"])  # type: ignore[return-value]

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM approval_requests WHERE approval_id = ?", (approval_id,)).fetchone()
            return dict(row) if row else None

    def list_approvals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM approval_requests WHERE status = ? ORDER BY created_at DESC", (status,)
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM approval_requests ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def decide_approval(self, approval_id: str, status: str, decided_by: str, comment: str) -> Optional[Dict[str, Any]]:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                UPDATE approval_requests SET status = ?, decided_by = ?, comment = ?, decided_at = ?
                WHERE approval_id = ?
                """,
                (status, decided_by, comment, now, approval_id),
            )
            self._conn.commit()
            return self.get_approval(approval_id)

    # --- Screenshots ---
    def save_screenshot(self, shot: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO screenshots (screenshot_id, action_id, window_id, width, height, simulated, image_b64, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    shot["screenshot_id"],
                    shot.get("action_id"),
                    shot.get("window_id"),
                    int(shot["width"]),
                    int(shot["height"]),
                    1 if shot.get("simulated", True) else 0,
                    shot["image_b64"],
                    shot["created_at"],
                ),
            )
            self._conn.commit()
            return shot

    def list_screenshots(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT screenshot_id, action_id, window_id, width, height, simulated, created_at FROM screenshots ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [{**dict(r), "simulated": bool(r["simulated"])} for r in rows]

    def get_screenshot(self, screenshot_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM screenshots WHERE screenshot_id = ?", (screenshot_id,)).fetchone()
            return {**dict(row), "simulated": bool(row["simulated"])} if row else None

    # --- Diagnostic Logs ---
    def add_log(
        self,
        event_type: str,
        message: str,
        level: str = "INFO",
        action_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO diagnostic_logs (action_id, level, event_type, message, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (action_id, level, event_type, message, json.dumps(details or {}), now),
            )
            self._conn.commit()
            return {
                "log_id": cur.lastrowid,
                "action_id": action_id,
                "level": level,
                "event_type": event_type,
                "message": message,
                "details": details or {},
                "created_at": now,
            }

    def list_logs(self, limit: int = 120) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM diagnostic_logs ORDER BY log_id DESC LIMIT ?", (limit,)).fetchall()
            return [
                {
                    "log_id": r["log_id"],
                    "action_id": r["action_id"],
                    "level": r["level"],
                    "event_type": r["event_type"],
                    "message": r["message"],
                    "details": json.loads(r["details_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
