"""SQLite WAL persistence for Module 21 browser sessions, workflows, approvals, downloads, and logs."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BrowserAgentDB:
    def __init__(self, db_path: str = "./data/jarvis_browser_agent.db") -> None:
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
            CREATE TABLE IF NOT EXISTS browser_sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                current_url TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                history_json TEXT NOT NULL DEFAULT '[]',
                form_state_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS browser_tasks (
                task_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                current_step INTEGER NOT NULL DEFAULT 0,
                steps_json TEXT NOT NULL,
                results_json TEXT NOT NULL DEFAULT '[]',
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES browser_sessions(session_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS submission_approvals (
                approval_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                task_id TEXT,
                url TEXT NOT NULL,
                form_id TEXT NOT NULL,
                fields_json TEXT NOT NULL DEFAULT '{}',
                prompt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                decided_by TEXT,
                comment TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            );

            CREATE TABLE IF NOT EXISTS downloads (
                download_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                filename TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                simulated INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS browser_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                task_id TEXT,
                level TEXT NOT NULL DEFAULT 'INFO',
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS site_policy (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def get_policy_raw(self, key: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute("SELECT value FROM site_policy WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    def set_policy_raw(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO site_policy(key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, value, utc_now_iso()),
            )
            self._conn.commit()

    # --- Sessions ---
    def create_session(self, s: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO browser_sessions (session_id, name, current_url, status, history_json, form_state_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    s["session_id"], s["name"], s["current_url"], s.get("status", "active"),
                    json.dumps(s.get("history", [])), json.dumps(s.get("form_state", {})),
                    s["created_at"], s["updated_at"],
                ),
            )
            self._conn.commit()
            return self.get_session(s["session_id"])  # type: ignore[return-value]

    def _row_to_session(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "session_id": r["session_id"], "name": r["name"], "current_url": r["current_url"],
            "status": r["status"], "history": json.loads(r["history_json"]),
            "form_state": json.loads(r["form_state_json"]),
            "created_at": r["created_at"], "updated_at": r["updated_at"],
        }

    def get_session(self, sid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM browser_sessions WHERE session_id = ?", (sid,)).fetchone()
            return self._row_to_session(r) if r else None

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [self._row_to_session(r) for r in self._conn.execute("SELECT * FROM browser_sessions ORDER BY updated_at DESC").fetchall()]

    def update_session(self, sid: str, **fields: Any) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        for k, v in fields.items():
            if k == "history":
                payload["history_json"] = json.dumps(v)
            elif k == "form_state":
                payload["form_state_json"] = json.dumps(v)
            elif k in ("current_url", "status", "name"):
                payload[k] = v
        payload["updated_at"] = utc_now_iso()
        cols = ", ".join(f"{k} = ?" for k in payload)
        with self._lock:
            self._conn.execute(f"UPDATE browser_sessions SET {cols} WHERE session_id = ?", list(payload.values()) + [sid])
            self._conn.commit()
            return self.get_session(sid)

    # --- Tasks ---
    def create_task(self, t: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO browser_tasks (task_id, session_id, name, status, current_step, steps_json, results_json, error, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t["task_id"], t["session_id"], t["name"], t["status"], int(t.get("current_step", 0)),
                    json.dumps(t["steps"]), json.dumps(t.get("results", [])), t.get("error"),
                    t["created_at"], t["updated_at"],
                ),
            )
            self._conn.commit()
            return self.get_task(t["task_id"])  # type: ignore[return-value]

    def _row_to_task(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "task_id": r["task_id"], "session_id": r["session_id"], "name": r["name"],
            "status": r["status"], "current_step": r["current_step"],
            "steps": json.loads(r["steps_json"]), "results": json.loads(r["results_json"]),
            "error": r["error"], "created_at": r["created_at"], "updated_at": r["updated_at"],
        }

    def get_task(self, tid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM browser_tasks WHERE task_id = ?", (tid,)).fetchone()
            return self._row_to_task(r) if r else None

    def list_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [self._row_to_task(r) for r in self._conn.execute("SELECT * FROM browser_tasks ORDER BY created_at DESC LIMIT 100").fetchall()]

    def update_task(self, tid: str, **fields: Any) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        for k, v in fields.items():
            if k == "results":
                payload["results_json"] = json.dumps(v)
            elif k in ("status", "current_step", "error"):
                payload[k] = v
        payload["updated_at"] = utc_now_iso()
        cols = ", ".join(f"{k} = ?" for k in payload)
        with self._lock:
            self._conn.execute(f"UPDATE browser_tasks SET {cols} WHERE task_id = ?", list(payload.values()) + [tid])
            self._conn.commit()
            return self.get_task(tid)

    # --- Approvals ---
    def create_approval(self, a: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO submission_approvals (approval_id, session_id, task_id, url, form_id, fields_json, prompt, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    a["approval_id"], a["session_id"], a.get("task_id"), a["url"], a["form_id"],
                    json.dumps(a.get("fields", {})), a["prompt"], "pending", a["created_at"],
                ),
            )
            self._conn.commit()
            return self.get_approval(a["approval_id"])  # type: ignore[return-value]

    def _row_to_approval(self, r: sqlite3.Row) -> Dict[str, Any]:
        d = dict(r)
        d["fields"] = json.loads(d.pop("fields_json"))
        return d

    def get_approval(self, aid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM submission_approvals WHERE approval_id = ?", (aid,)).fetchone()
            return self._row_to_approval(r) if r else None

    def list_approvals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute("SELECT * FROM submission_approvals WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM submission_approvals ORDER BY created_at DESC").fetchall()
            return [self._row_to_approval(r) for r in rows]

    def decide_approval(self, aid: str, status: str, decided_by: str, comment: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._conn.execute(
                "UPDATE submission_approvals SET status = ?, decided_by = ?, comment = ?, decided_at = ? WHERE approval_id = ?",
                (status, decided_by, comment, utc_now_iso(), aid),
            )
            self._conn.commit()
            return self.get_approval(aid)

    # --- Downloads & Logs ---
    def record_download(self, d: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                "INSERT INTO downloads (download_id, session_id, source_url, filename, size_bytes, sha256, simulated, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (d["download_id"], d["session_id"], d["source_url"], d["filename"], d["size_bytes"], d["sha256"], 1 if d.get("simulated", True) else 0, d["created_at"]),
            )
            self._conn.commit()
            return d

    def list_downloads(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM downloads ORDER BY created_at DESC LIMIT 100").fetchall()
            return [{**dict(r), "simulated": bool(r["simulated"])} for r in rows]

    def add_log(self, event_type: str, message: str, level: str = "INFO", session_id: Optional[str] = None, task_id: Optional[str] = None) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO browser_logs (session_id, task_id, level, event_type, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, task_id, level, event_type, message, now),
            )
            self._conn.commit()
            return {"log_id": cur.lastrowid, "session_id": session_id, "task_id": task_id, "level": level, "event_type": event_type, "message": message, "created_at": now}

    def list_logs(self, limit: int = 120) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._conn.execute("SELECT * FROM browser_logs ORDER BY log_id DESC LIMIT ?", (limit,)).fetchall()]
