"""SQLite WAL persistence layer for JARVIS Module 35 — Visual Workflow Builder."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowDB:
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
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    nodes_json TEXT NOT NULL,
                    edges_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    trace_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
                );
                """
            )

    def _wf_row(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "workflow_id": r["workflow_id"],
            "name": r["name"],
            "description": r["description"],
            "nodes": json.loads(r["nodes_json"]),
            "edges": json.loads(r["edges_json"]),
            "created_at": r["created_at"],
        }

    def create_workflow(self, wf: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflows (workflow_id, name, description, nodes_json, edges_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    wf["workflow_id"],
                    wf["name"],
                    wf["description"],
                    json.dumps(wf["nodes"]),
                    json.dumps(wf["edges"]),
                    wf["created_at"],
                ),
            )
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,)).fetchone()
            return self._wf_row(row) if row else None

    def list_workflows(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM workflows ORDER BY created_at DESC").fetchall()
            return [self._wf_row(r) for r in rows]

    def add_run(self, run: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_runs (run_id, workflow_id, status, input_json, context_json, trace_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run["run_id"],
                    run["workflow_id"],
                    run["status"],
                    json.dumps(run["input_data"]),
                    json.dumps(run["final_context"]),
                    json.dumps(run["trace"]),
                    run["created_at"],
                ),
            )
        return run

    def list_runs(self, workflow_id: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if workflow_id:
                rows = conn.execute(
                    "SELECT * FROM workflow_runs WHERE workflow_id = ? ORDER BY created_at DESC LIMIT ?",
                    (workflow_id, limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [
                {
                    "run_id": r["run_id"],
                    "workflow_id": r["workflow_id"],
                    "status": r["status"],
                    "input_data": json.loads(r["input_json"]),
                    "final_context": json.loads(r["context_json"]),
                    "trace": json.loads(r["trace_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
