"""Isolated SQLite WAL persistence for JARVIS Module 26 — Project Autopilot."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectAutopilotDB:
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
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    tech_stack_json TEXT NOT NULL,
                    dry_run INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'planned',
                    workspace_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS milestones (
                    milestone_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    order_index INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    milestone_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    depends_on_json TEXT NOT NULL,
                    requires_approval INTEGER NOT NULL DEFAULT 0,
                    approval_status TEXT NOT NULL DEFAULT 'not_required',
                    status TEXT NOT NULL DEFAULT 'pending',
                    estimated_minutes INTEGER NOT NULL DEFAULT 30,
                    output_summary TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                    FOREIGN KEY(milestone_id) REFERENCES milestones(milestone_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS execution_logs (
                    log_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    task_id TEXT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                );
                """
            )

    def _row_to_project(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "project_id": row["project_id"],
            "name": row["name"],
            "slug": row["slug"],
            "goal": row["goal"],
            "tech_stack": json.loads(row["tech_stack_json"]),
            "dry_run": bool(row["dry_run"]),
            "status": row["status"],
            "workspace_path": row["workspace_path"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _row_to_task(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "task_id": row["task_id"],
            "project_id": row["project_id"],
            "milestone_id": row["milestone_id"],
            "title": row["title"],
            "description": row["description"],
            "depends_on": json.loads(row["depends_on_json"]),
            "requires_approval": bool(row["requires_approval"]),
            "approval_status": row["approval_status"],
            "status": row["status"],
            "estimated_minutes": row["estimated_minutes"],
            "output_summary": row["output_summary"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def create_project(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects (project_id, name, slug, goal, tech_stack_json, dry_run, status, workspace_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["project_id"],
                    rec["name"],
                    rec["slug"],
                    rec["goal"],
                    json.dumps(rec["tech_stack"]),
                    1 if rec["dry_run"] else 0,
                    rec["status"],
                    rec.get("workspace_path"),
                    rec["created_at"],
                    rec["updated_at"],
                ),
            )
        return self.get_project(rec["project_id"])  # type: ignore[return-value]

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
            return self._row_to_project(row) if row else None

    def list_projects(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
            return [self._row_to_project(r) for r in rows]

    def update_project(self, project_id: str, status: Optional[str] = None, workspace_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            cur = self.get_project(project_id)
            if not cur:
                return None
            conn.execute(
                "UPDATE projects SET status = ?, workspace_path = ?, updated_at = ? WHERE project_id = ?",
                (status or cur["status"], workspace_path if workspace_path is not None else cur["workspace_path"], utc_now_iso(), project_id),
            )
        return self.get_project(project_id)

    def create_milestone(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO milestones (milestone_id, project_id, order_index, title, objective, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (rec["milestone_id"], rec["project_id"], rec["order_index"], rec["title"], rec["objective"], rec["status"], rec["created_at"]),
            )
            row = conn.execute("SELECT * FROM milestones WHERE milestone_id = ?", (rec["milestone_id"],)).fetchone()
            return dict(row)

    def list_milestones(self, project_id: str) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM milestones WHERE project_id = ? ORDER BY order_index ASC",
                (project_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_milestone_status(self, milestone_id: str, status: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE milestones SET status = ? WHERE milestone_id = ?", (status, milestone_id))

    def create_task(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, project_id, milestone_id, title, description, depends_on_json,
                    requires_approval, approval_status, status, estimated_minutes, output_summary, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["task_id"],
                    rec["project_id"],
                    rec["milestone_id"],
                    rec["title"],
                    rec["description"],
                    json.dumps(rec["depends_on"]),
                    1 if rec["requires_approval"] else 0,
                    rec["approval_status"],
                    rec["status"],
                    rec["estimated_minutes"],
                    rec.get("output_summary"),
                    rec["created_at"],
                    rec["updated_at"],
                ),
            )
        return self.get_task(rec["task_id"])  # type: ignore[return-value]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            return self._row_to_task(row) if row else None

    def list_tasks(self, project_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            q = "SELECT * FROM tasks WHERE 1=1"
            params: List[Any] = []
            if project_id:
                q += " AND project_id = ?"
                params.append(project_id)
            if status:
                q += " AND status = ?"
                params.append(status)
            q += " ORDER BY created_at ASC"
            rows = conn.execute(q, params).fetchall()
            return [self._row_to_task(r) for r in rows]

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        approval_status: Optional[str] = None,
        output_summary: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            cur = self.get_task(task_id)
            if not cur:
                return None
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, approval_status = ?, output_summary = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (
                    status or cur["status"],
                    approval_status or cur["approval_status"],
                    output_summary if output_summary is not None else cur["output_summary"],
                    utc_now_iso(),
                    task_id,
                ),
            )
        return self.get_task(task_id)

    def add_log(self, log_id: str, project_id: str, level: str, message: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO execution_logs (log_id, project_id, task_id, level, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (log_id, project_id, task_id, level, message, now),
            )
        return {"log_id": log_id, "project_id": project_id, "task_id": task_id, "level": level, "message": message, "created_at": now}

    def list_logs(self, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM execution_logs WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
                (project_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
