"""SQLite WAL persistence layer for JARVIS Module 43 — Autonomous Screen Guardian."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ScreenGuardianDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA foreign_keys=ON;")
            self._init_schema()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS detected_errors (
                error_id TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                source_app TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                likely_cause TEXT NOT NULL,
                confidence REAL NOT NULL,
                suggested_action TEXT NOT NULL,
                repair_available INTEGER NOT NULL DEFAULT 1,
                occurrences INTEGER NOT NULL DEFAULT 1,
                ignored INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                error_id TEXT,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                application TEXT NOT NULL,
                details TEXT NOT NULL,
                suggested_action TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'unread',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ocr_history (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                frame_hash TEXT NOT NULL,
                source_app TEXT NOT NULL,
                ocr_engine TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                confidence REAL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS repair_jobs (
                repair_id TEXT PRIMARY KEY,
                error_id TEXT,
                workspace_path TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                outcome TEXT NOT NULL DEFAULT 'approval_required',
                summary TEXT NOT NULL,
                error_context TEXT NOT NULL DEFAULT '',
                approval_status TEXT NOT NULL DEFAULT 'pending',
                reviewer TEXT,
                plan_text TEXT,
                diff_text TEXT,
                changed_files_json TEXT NOT NULL DEFAULT '[]',
                test_results_json TEXT NOT NULL DEFAULT '{}',
                logs_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL DEFAULT 'INFO',
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                setting_id INTEGER PRIMARY KEY CHECK (setting_id = 1),
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    # --- Errors ---
    def upsert_error(self, data: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        """Insert or deduplicate an error by fingerprint. Returns (error_dict, is_new)."""
        now = utc_now_iso()
        with self._lock:
            existing = self._conn.execute(
                "SELECT * FROM detected_errors WHERE fingerprint = ?", (data["fingerprint"],)
            ).fetchone()
            if existing:
                new_status = "ongoing" if existing["status"] in {"new", "ongoing"} else existing["status"]
                self._conn.execute(
                    """
                    UPDATE detected_errors
                    SET occurrences = occurrences + 1, status = ?, last_seen_at = ?, extracted_text = ?
                    WHERE error_id = ?
                    """,
                    (new_status, now, data["extracted_text"], existing["error_id"]),
                )
                self._conn.commit()
                row = self._conn.execute(
                    "SELECT * FROM detected_errors WHERE error_id = ?", (existing["error_id"],)
                ).fetchone()
                assert row is not None
                return dict(row), False

            self._conn.execute(
                """
                INSERT INTO detected_errors (
                    error_id, fingerprint, title, category, severity, status, source_app,
                    extracted_text, likely_cause, confidence, suggested_action,
                    repair_available, occurrences, ignored, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?)
                """,
                (
                    data["error_id"],
                    data["fingerprint"],
                    data["title"],
                    data["category"],
                    data["severity"],
                    data.get("status", "new"),
                    data["source_app"],
                    data["extracted_text"],
                    data["likely_cause"],
                    float(data["confidence"]),
                    data["suggested_action"],
                    1 if data.get("repair_available", True) else 0,
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM detected_errors WHERE error_id = ?", (data["error_id"],)).fetchone()
            assert row is not None
            return dict(row), True

    def list_errors(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM detected_errors WHERE status = ? ORDER BY last_seen_at DESC LIMIT ?", (status, limit)
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM detected_errors ORDER BY last_seen_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    def get_error(self, error_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM detected_errors WHERE error_id = ?", (error_id,)).fetchone()
            return dict(row) if row else None

    def update_error(self, error_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        allowed = {"status", "ignored"}
        payload = {k: v for k, v in fields.items() if k in allowed}
        if not payload:
            return self.get_error(error_id)
        payload["last_seen_at"] = utc_now_iso()
        cols = ", ".join(f"{k} = ?" for k in payload)
        with self._lock:
            self._conn.execute(f"UPDATE detected_errors SET {cols} WHERE error_id = ?", list(payload.values()) + [error_id])
            self._conn.commit()
        return self.get_error(error_id)

    # --- Notifications ---
    def add_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO notifications (
                    notification_id, error_id, category, severity, title, application,
                    details, suggested_action, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'unread', ?, ?)
                """,
                (
                    data["notification_id"],
                    data.get("error_id"),
                    data["category"],
                    data["severity"],
                    data["title"],
                    data["application"],
                    data["details"],
                    data["suggested_action"],
                    now,
                    now,
                ),
            )
            self._conn.commit()
            return self.get_notification(data["notification_id"])  # type: ignore[return-value]

    def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM notifications WHERE notification_id = ?", (notification_id,)).fetchone()
            return dict(row) if row else None

    def list_notifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def update_notification_status(self, notification_id: str, status: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._conn.execute(
                "UPDATE notifications SET status = ?, updated_at = ? WHERE notification_id = ?",
                (status, utc_now_iso(), notification_id),
            )
            self._conn.commit()
        return self.get_notification(notification_id)

    # --- OCR History ---
    def add_ocr_entry(self, frame_hash: str, source_app: str, ocr_engine: str, text: str, confidence: Optional[float]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO ocr_history (frame_hash, source_app, ocr_engine, extracted_text, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (frame_hash, source_app, ocr_engine, text, confidence, now),
            )
            self._conn.commit()
            return {
                "entry_id": cur.lastrowid,
                "frame_hash": frame_hash,
                "source_app": source_app,
                "ocr_engine": ocr_engine,
                "extracted_text": text,
                "confidence": confidence,
                "created_at": now,
            }

    def list_ocr_history(self, query: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            if query:
                rows = self._conn.execute(
                    "SELECT * FROM ocr_history WHERE extracted_text LIKE ? ORDER BY entry_id DESC LIMIT ?",
                    (f"%{query}%", limit),
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM ocr_history ORDER BY entry_id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    # --- Repair Jobs ---
    @staticmethod
    def _row_to_repair(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "repair_id": row["repair_id"],
            "error_id": row["error_id"],
            "workspace_path": row["workspace_path"],
            "agent_id": row["agent_id"],
            "mode": row["mode"],
            "status": row["status"],
            "outcome": row["outcome"],
            "summary": row["summary"],
            "error_context": row["error_context"],
            "approval_status": row["approval_status"],
            "reviewer": row["reviewer"],
            "plan_text": row["plan_text"],
            "diff_text": row["diff_text"],
            "changed_files": json.loads(row["changed_files_json"]),
            "test_results": json.loads(row["test_results_json"]),
            "logs": json.loads(row["logs_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "completed_at": row["completed_at"],
        }

    def create_repair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO repair_jobs (
                    repair_id, error_id, workspace_path, agent_id, mode, status, outcome,
                    summary, error_context, approval_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["repair_id"],
                    data.get("error_id"),
                    data["workspace_path"],
                    data["agent_id"],
                    data["mode"],
                    data["status"],
                    data.get("outcome", "approval_required"),
                    data["summary"],
                    data.get("error_context", ""),
                    data.get("approval_status", "pending"),
                    now,
                    now,
                ),
            )
            self._conn.commit()
            return self.get_repair(data["repair_id"])  # type: ignore[return-value]

    def get_repair(self, repair_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM repair_jobs WHERE repair_id = ?", (repair_id,)).fetchone()
            return self._row_to_repair(row) if row else None

    def list_repairs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM repair_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [self._row_to_repair(r) for r in rows]

    def update_repair(self, repair_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        for k, v in fields.items():
            if k == "changed_files":
                payload["changed_files_json"] = json.dumps(v)
            elif k == "test_results":
                payload["test_results_json"] = json.dumps(v)
            elif k == "logs":
                payload["logs_json"] = json.dumps(v)
            elif k in {"status", "outcome", "approval_status", "reviewer", "plan_text", "diff_text", "completed_at"}:
                payload[k] = v
        payload["updated_at"] = utc_now_iso()
        cols = ", ".join(f"{k} = ?" for k in payload)
        with self._lock:
            self._conn.execute(f"UPDATE repair_jobs SET {cols} WHERE repair_id = ?", list(payload.values()) + [repair_id])
            self._conn.commit()
        return self.get_repair(repair_id)

    # --- Audit Logs & Settings ---
    def add_log(self, event_type: str, message: str, level: str = "INFO", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO audit_logs (level, event_type, message, details_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (level, event_type, message, json.dumps(details or {}), now),
            )
            self._conn.commit()
            return {"log_id": cur.lastrowid, "level": level, "event_type": event_type, "message": message, "details": details or {}, "created_at": now}

    def list_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT ?", (limit,)).fetchall()
            return [{"log_id": r["log_id"], "level": r["level"], "event_type": r["event_type"], "message": r["message"], "details": json.loads(r["details_json"]), "created_at": r["created_at"]} for r in rows]

    def save_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings (setting_id, data_json, updated_at) VALUES (1, ?, ?) ON CONFLICT(setting_id) DO UPDATE SET data_json=excluded.data_json, updated_at=excluded.updated_at",
                (json.dumps(data), now),
            )
            self._conn.commit()
        return data

    def load_settings(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT data_json FROM settings WHERE setting_id = 1").fetchone()
            return json.loads(row["data_json"]) if row else None
