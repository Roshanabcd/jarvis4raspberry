"""Isolated SQLite WAL persistence for JARVIS Module 27 — GitHub & CI/CD Manager."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GitHubCICDDB:
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
                CREATE TABLE IF NOT EXISTS repositories (
                    repo_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL UNIQUE,
                    default_branch TEXT NOT NULL,
                    require_ci_green INTEGER NOT NULL DEFAULT 1,
                    workflows_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pull_requests (
                    pr_id TEXT PRIMARY KEY,
                    repo_id TEXT NOT NULL,
                    pr_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    source_branch TEXT NOT NULL,
                    target_branch TEXT NOT NULL,
                    author TEXT NOT NULL,
                    files_changed INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    ci_status TEXT NOT NULL DEFAULT 'pending',
                    merge_strategy TEXT,
                    merged_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id TEXT PRIMARY KEY,
                    repo_id TEXT NOT NULL,
                    pr_id TEXT,
                    workflow_name TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_sec REAL NOT NULL,
                    steps_json TEXT NOT NULL,
                    simulated INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS releases (
                    release_id TEXT PRIMARY KEY,
                    repo_id TEXT NOT NULL,
                    tag_name TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'published',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE
                );
                """
            )

    def _row_repo(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "repo_id": r["repo_id"],
            "full_name": r["full_name"],
            "default_branch": r["default_branch"],
            "require_ci_green": bool(r["require_ci_green"]),
            "workflows": json.loads(r["workflows_json"]),
            "created_at": r["created_at"],
        }

    def _row_run(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "run_id": r["run_id"],
            "repo_id": r["repo_id"],
            "pr_id": r["pr_id"],
            "workflow_name": r["workflow_name"],
            "branch": r["branch"],
            "status": r["status"],
            "duration_sec": r["duration_sec"],
            "steps": json.loads(r["steps_json"]),
            "simulated": bool(r["simulated"]),
            "created_at": r["created_at"],
        }

    def create_repo(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO repositories (repo_id, full_name, default_branch, require_ci_green, workflows_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["repo_id"],
                    rec["full_name"],
                    rec["default_branch"],
                    1 if rec["require_ci_green"] else 0,
                    json.dumps(rec["workflows"]),
                    rec["created_at"],
                ),
            )
        return self.get_repo(rec["repo_id"])  # type: ignore[return-value]

    def get_repo(self, repo_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM repositories WHERE repo_id = ?", (repo_id,)).fetchone()
            return self._row_repo(row) if row else None

    def get_repo_by_name(self, full_name: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM repositories WHERE full_name = ?", (full_name,)).fetchone()
            return self._row_repo(row) if row else None

    def list_repos(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM repositories ORDER BY created_at DESC").fetchall()
            return [self._row_repo(r) for r in rows]

    def next_pr_number(self, repo_id: str) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT COALESCE(MAX(pr_number), 0) AS mx FROM pull_requests WHERE repo_id = ?", (repo_id,)).fetchone()
            return int(row["mx"]) + 1

    def create_pr(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pull_requests (
                    pr_id, repo_id, pr_number, title, source_branch, target_branch, author,
                    files_changed, status, ci_status, merge_strategy, merged_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["pr_id"],
                    rec["repo_id"],
                    rec["pr_number"],
                    rec["title"],
                    rec["source_branch"],
                    rec["target_branch"],
                    rec["author"],
                    rec["files_changed"],
                    rec["status"],
                    rec["ci_status"],
                    rec.get("merge_strategy"),
                    rec.get("merged_at"),
                    rec["created_at"],
                ),
            )
        return self.get_pr(rec["pr_id"])  # type: ignore[return-value]

    def get_pr(self, pr_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM pull_requests WHERE pr_id = ?", (pr_id,)).fetchone()
            return dict(row) if row else None

    def list_prs(self, repo_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            q = "SELECT * FROM pull_requests WHERE 1=1"
            params: List[Any] = []
            if repo_id:
                q += " AND repo_id = ?"
                params.append(repo_id)
            if status:
                q += " AND status = ?"
                params.append(status)
            q += " ORDER BY created_at DESC"
            return [dict(r) for r in conn.execute(q, params).fetchall()]

    def update_pr(
        self,
        pr_id: str,
        status: Optional[str] = None,
        ci_status: Optional[str] = None,
        merge_strategy: Optional[str] = None,
        merged_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            cur = self.get_pr(pr_id)
            if not cur:
                return None
            conn.execute(
                """
                UPDATE pull_requests
                SET status = ?, ci_status = ?, merge_strategy = ?, merged_at = ?
                WHERE pr_id = ?
                """,
                (
                    status or cur["status"],
                    ci_status or cur["ci_status"],
                    merge_strategy if merge_strategy is not None else cur["merge_strategy"],
                    merged_at if merged_at is not None else cur["merged_at"],
                    pr_id,
                ),
            )
        return self.get_pr(pr_id)

    def create_run(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pipeline_runs (
                    run_id, repo_id, pr_id, workflow_name, branch, status, duration_sec, steps_json, simulated, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["run_id"],
                    rec["repo_id"],
                    rec.get("pr_id"),
                    rec["workflow_name"],
                    rec["branch"],
                    rec["status"],
                    rec["duration_sec"],
                    json.dumps(rec["steps"]),
                    1 if rec["simulated"] else 0,
                    rec["created_at"],
                ),
            )
        return self.get_run(rec["run_id"])  # type: ignore[return-value]

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM pipeline_runs WHERE run_id = ?", (run_id,)).fetchone()
            return self._row_run(row) if row else None

    def list_runs(self, repo_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if repo_id:
                rows = conn.execute("SELECT * FROM pipeline_runs WHERE repo_id = ? ORDER BY created_at DESC", (repo_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM pipeline_runs ORDER BY created_at DESC").fetchall()
            return [self._row_run(r) for r in rows]

    def create_release(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO releases (release_id, repo_id, tag_name, notes, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (rec["release_id"], rec["repo_id"], rec["tag_name"], rec["notes"], rec["status"], rec["created_at"]),
            )
            row = conn.execute("SELECT * FROM releases WHERE release_id = ?", (rec["release_id"],)).fetchone()
            return dict(row)

    def list_releases(self, repo_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if repo_id:
                rows = conn.execute("SELECT * FROM releases WHERE repo_id = ? ORDER BY created_at DESC", (repo_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM releases ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def update_release_status(self, release_id: str, status: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE releases SET status = ? WHERE release_id = ?", (status, release_id))
            row = conn.execute("SELECT * FROM releases WHERE release_id = ?", (release_id,)).fetchone()
            return dict(row) if row else None
