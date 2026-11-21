"""SQLite WAL persistence layer for JARVIS Module 18."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OrchestratorDatabase:
    """Thread-safe SQLite WAL database for persistent multi-agent orchestration state."""

    def __init__(self, db_path: str = "./data/jarvis_orchestrator.db") -> None:
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
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                capabilities_json TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'online',
                max_concurrency INTEGER NOT NULL DEFAULT 2,
                completed_tasks INTEGER NOT NULL DEFAULT 0,
                failed_tasks INTEGER NOT NULL DEFAULT 0,
                handler_type TEXT NOT NULL DEFAULT 'research',
                simulated INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                registered_at TEXT NOT NULL,
                last_heartbeat TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                required_capability TEXT,
                assigned_agent_id TEXT,
                priority INTEGER NOT NULL DEFAULT 2,
                status TEXT NOT NULL DEFAULT 'pending',
                payload_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT,
                error TEXT,
                retries_attempted INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 2,
                retry_backoff_sec REAL NOT NULL DEFAULT 0.25,
                timeout_sec REAL NOT NULL DEFAULT 15.0,
                requires_approval INTEGER NOT NULL DEFAULT 0,
                approval_status TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS task_dependencies (
                task_id TEXT NOT NULL,
                depends_on_task_id TEXT NOT NULL,
                PRIMARY KEY (task_id, depends_on_task_id),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
                FOREIGN KEY (depends_on_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS approval_requests (
                approval_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL UNIQUE,
                workflow_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                decided_by TEXT,
                comment TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS agent_messages (
                message_id TEXT PRIMARY KEY,
                sender_agent_id TEXT NOT NULL,
                recipient_agent_id TEXT NOT NULL,
                task_id TEXT,
                workflow_id TEXT,
                channel TEXT NOT NULL DEFAULT 'coordination',
                content TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS execution_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                agent_id TEXT,
                level TEXT NOT NULL DEFAULT 'INFO',
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS engine_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority DESC, created_at ASC);
            CREATE INDEX IF NOT EXISTS idx_tasks_workflow ON tasks(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_logs_task ON execution_logs(task_id);
            CREATE INDEX IF NOT EXISTS idx_messages_workflow ON agent_messages(workflow_id);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # --- Settings ---
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._lock:
            row = self._conn.execute("SELECT value FROM engine_settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO engine_settings(key, value, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, now),
            )
            self._conn.commit()

    # --- Agents ---
    def upsert_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO agents (
                    agent_id, name, role, capabilities_json, status, max_concurrency,
                    completed_tasks, failed_tasks, handler_type, simulated, metadata_json,
                    registered_at, last_heartbeat
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    name=excluded.name,
                    role=excluded.role,
                    capabilities_json=excluded.capabilities_json,
                    status=excluded.status,
                    max_concurrency=excluded.max_concurrency,
                    handler_type=excluded.handler_type,
                    simulated=excluded.simulated,
                    metadata_json=excluded.metadata_json,
                    last_heartbeat=excluded.last_heartbeat
                """,
                (
                    agent["agent_id"],
                    agent["name"],
                    agent["role"],
                    json.dumps(agent.get("capabilities", [])),
                    agent.get("status", "online"),
                    int(agent.get("max_concurrency", 2)),
                    int(agent.get("completed_tasks", 0)),
                    int(agent.get("failed_tasks", 0)),
                    agent.get("handler_type", "research"),
                    1 if agent.get("simulated", True) else 0,
                    json.dumps(agent.get("metadata", {})),
                    agent["registered_at"],
                    agent["last_heartbeat"],
                ),
            )
            self._conn.commit()
            return self.get_agent(agent["agent_id"])  # type: ignore[return-value]

    def _row_to_agent(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "agent_id": row["agent_id"],
            "name": row["name"],
            "role": row["role"],
            "capabilities": json.loads(row["capabilities_json"]),
            "status": row["status"],
            "max_concurrency": row["max_concurrency"],
            "completed_tasks": row["completed_tasks"],
            "failed_tasks": row["failed_tasks"],
            "handler_type": row["handler_type"],
            "simulated": bool(row["simulated"]),
            "metadata": json.loads(row["metadata_json"]),
            "registered_at": row["registered_at"],
            "last_heartbeat": row["last_heartbeat"],
        }

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,)).fetchone()
            return self._row_to_agent(row) if row else None

    def list_agents(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM agents ORDER BY registered_at ASC").fetchall()
            return [self._row_to_agent(r) for r in rows]

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_agent(agent_id)
        if not existing:
            return None
        existing.update({k: v for k, v in updates.items() if v is not None})
        existing["last_heartbeat"] = utc_now_iso()
        return self.upsert_agent(existing)

    def increment_agent_counter(self, agent_id: str, field: str) -> None:
        if field not in ("completed_tasks", "failed_tasks"):
            return
        with self._lock:
            self._conn.execute(
                f"UPDATE agents SET {field} = {field} + 1, last_heartbeat = ? WHERE agent_id = ?",
                (utc_now_iso(), agent_id),
            )
            self._conn.commit()

    def delete_agent(self, agent_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
            self._conn.commit()
            return cur.rowcount > 0

    # --- Tasks & Dependencies ---
    def create_task(self, task: Dict[str, Any], depends_on: List[str]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO tasks (
                    task_id, workflow_id, title, description, required_capability,
                    assigned_agent_id, priority, status, payload_json, result_json, error,
                    retries_attempted, max_retries, retry_backoff_sec, timeout_sec,
                    requires_approval, approval_status, created_at, updated_at, started_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task["task_id"],
                    task["workflow_id"],
                    task["title"],
                    task.get("description", ""),
                    task.get("required_capability"),
                    task.get("assigned_agent_id"),
                    int(task.get("priority", 2)),
                    task.get("status", "pending"),
                    json.dumps(task.get("payload", {})),
                    json.dumps(task["result"]) if task.get("result") is not None else None,
                    task.get("error"),
                    int(task.get("retries_attempted", 0)),
                    int(task.get("max_retries", 2)),
                    float(task.get("retry_backoff_sec", 0.25)),
                    float(task.get("timeout_sec", 15.0)),
                    1 if task.get("requires_approval") else 0,
                    task.get("approval_status"),
                    task["created_at"],
                    task["updated_at"],
                    task.get("started_at"),
                    task.get("completed_at"),
                ),
            )
            for dep_id in depends_on:
                self._conn.execute(
                    "INSERT OR IGNORE INTO task_dependencies(task_id, depends_on_task_id) VALUES (?, ?)",
                    (task["task_id"], dep_id),
                )
            self._conn.commit()
            return self.get_task(task["task_id"])  # type: ignore[return-value]

    def _get_dependencies(self, task_id: str) -> List[str]:
        rows = self._conn.execute(
            "SELECT depends_on_task_id FROM task_dependencies WHERE task_id = ? ORDER BY depends_on_task_id ASC",
            (task_id,),
        ).fetchall()
        return [r["depends_on_task_id"] for r in rows]

    def get_dependents(self, task_id: str) -> List[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT task_id FROM task_dependencies WHERE depends_on_task_id = ?",
                (task_id,),
            ).fetchall()
            return [r["task_id"] for r in rows]

    def _row_to_task(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "task_id": row["task_id"],
            "workflow_id": row["workflow_id"],
            "title": row["title"],
            "description": row["description"],
            "required_capability": row["required_capability"],
            "assigned_agent_id": row["assigned_agent_id"],
            "priority": row["priority"],
            "status": row["status"],
            "depends_on": self._get_dependencies(row["task_id"]),
            "payload": json.loads(row["payload_json"]),
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
            "error": row["error"],
            "retries_attempted": row["retries_attempted"],
            "max_retries": row["max_retries"],
            "retry_backoff_sec": row["retry_backoff_sec"],
            "timeout_sec": row["timeout_sec"],
            "requires_approval": bool(row["requires_approval"]),
            "approval_status": row["approval_status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
        }

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            return self._row_to_task(row) if row else None

    def list_tasks(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            clauses: List[str] = []
            params: List[Any] = []
            if workflow_id:
                clauses.append("workflow_id = ?")
                params.append(workflow_id)
            if status:
                clauses.append("status = ?")
                params.append(status)
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            params.append(limit)
            rows = self._conn.execute(
                f"SELECT * FROM tasks {where} ORDER BY priority DESC, created_at ASC LIMIT ?",
                params,
            ).fetchall()
            return [self._row_to_task(r) for r in rows]

    def update_task_fields(self, task_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        if not fields:
            return self.get_task(task_id)
        allowed = {
            "assigned_agent_id",
            "status",
            "result_json",
            "error",
            "retries_attempted",
            "approval_status",
            "started_at",
            "completed_at",
            "priority",
        }
        payload: Dict[str, Any] = {}
        for k, v in fields.items():
            if k == "result":
                payload["result_json"] = json.dumps(v) if v is not None else None
            elif k in allowed:
                payload[k] = v
        payload["updated_at"] = utc_now_iso()
        cols = ", ".join(f"{k} = ?" for k in payload.keys())
        vals = list(payload.values()) + [task_id]
        with self._lock:
            self._conn.execute(f"UPDATE tasks SET {cols} WHERE task_id = ?", vals)
            self._conn.commit()
            return self.get_task(task_id)

    def get_all_dependency_edges(self, workflow_id: Optional[str] = None) -> List[Dict[str, str]]:
        with self._lock:
            if workflow_id:
                rows = self._conn.execute(
                    """
                    SELECT td.depends_on_task_id AS source, td.task_id AS target
                    FROM task_dependencies td
                    JOIN tasks t ON td.task_id = t.task_id
                    WHERE t.workflow_id = ?
                    """,
                    (workflow_id,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT depends_on_task_id AS source, task_id AS target FROM task_dependencies"
                ).fetchall()
            return [{"source": r["source"], "target": r["target"]} for r in rows]

    def reset_interrupted_running_tasks(self) -> int:
        """On restart, recover any tasks left in 'running' state back to 'queued'."""
        now = utc_now_iso()
        with self._lock:
            cur = self._conn.execute(
                "UPDATE tasks SET status = 'queued', updated_at = ? WHERE status = 'running'",
                (now,),
            )
            self._conn.commit()
            return cur.rowcount

    # --- Approvals ---
    def create_approval(self, approval: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO approval_requests (
                    approval_id, task_id, workflow_id, prompt, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    approval["approval_id"],
                    approval["task_id"],
                    approval["workflow_id"],
                    approval["prompt"],
                    approval.get("status", "pending"),
                    approval["created_at"],
                ),
            )
            self._conn.commit()
            return self.get_approval(approval["approval_id"])  # type: ignore[return-value]

    def _row_to_approval(self, row: sqlite3.Row) -> Dict[str, Any]:
        return dict(row)

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM approval_requests WHERE approval_id = ?", (approval_id,)
            ).fetchone()
            return self._row_to_approval(row) if row else None

    def get_approval_by_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM approval_requests WHERE task_id = ?", (task_id,)
            ).fetchone()
            return self._row_to_approval(row) if row else None

    def list_approvals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM approval_requests WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM approval_requests ORDER BY created_at DESC"
                ).fetchall()
            return [self._row_to_approval(r) for r in rows]

    def decide_approval(
        self, approval_id: str, status: str, decided_by: str, comment: str
    ) -> Optional[Dict[str, Any]]:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                UPDATE approval_requests
                SET status = ?, decided_by = ?, comment = ?, decided_at = ?
                WHERE approval_id = ?
                """,
                (status, decided_by, comment, now, approval_id),
            )
            self._conn.commit()
            return self.get_approval(approval_id)

    # --- Agent Messages ---
    def create_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO agent_messages (
                    message_id, sender_agent_id, recipient_agent_id, task_id,
                    workflow_id, channel, content, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg["message_id"],
                    msg["sender_agent_id"],
                    msg["recipient_agent_id"],
                    msg.get("task_id"),
                    msg.get("workflow_id"),
                    msg.get("channel", "coordination"),
                    msg["content"],
                    json.dumps(msg.get("metadata", {})),
                    msg["created_at"],
                ),
            )
            self._conn.commit()
            return msg

    def list_messages(
        self,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            clauses: List[str] = []
            params: List[Any] = []
            if workflow_id:
                clauses.append("workflow_id = ?")
                params.append(workflow_id)
            if agent_id:
                clauses.append("(sender_agent_id = ? OR recipient_agent_id = ? OR recipient_agent_id = 'broadcast')")
                params.extend([agent_id, agent_id])
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            params.append(limit)
            rows = self._conn.execute(
                f"SELECT * FROM agent_messages {where} ORDER BY created_at DESC LIMIT ?",
                params,
            ).fetchall()
            return [
                {
                    "message_id": r["message_id"],
                    "sender_agent_id": r["sender_agent_id"],
                    "recipient_agent_id": r["recipient_agent_id"],
                    "task_id": r["task_id"],
                    "workflow_id": r["workflow_id"],
                    "channel": r["channel"],
                    "content": r["content"],
                    "metadata": json.loads(r["metadata_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def count_messages(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS c FROM agent_messages").fetchone()
            return int(row["c"])

    # --- Execution Logs ---
    def add_log(
        self,
        event_type: str,
        message: str,
        level: str = "INFO",
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO execution_logs (task_id, agent_id, level, event_type, message, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, agent_id, level, event_type, message, json.dumps(details or {}), now),
            )
            self._conn.commit()
            return {
                "log_id": cur.lastrowid,
                "task_id": task_id,
                "agent_id": agent_id,
                "level": level,
                "event_type": event_type,
                "message": message,
                "details": details or {},
                "created_at": now,
            }

    def list_logs(
        self,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 150,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            clauses: List[str] = []
            params: List[Any] = []
            if task_id:
                clauses.append("task_id = ?")
                params.append(task_id)
            if agent_id:
                clauses.append("agent_id = ?")
                params.append(agent_id)
            if level:
                clauses.append("level = ?")
                params.append(level.upper())
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            params.append(limit)
            rows = self._conn.execute(
                f"SELECT * FROM execution_logs {where} ORDER BY log_id DESC LIMIT ?",
                params,
            ).fetchall()
            return [
                {
                    "log_id": r["log_id"],
                    "task_id": r["task_id"],
                    "agent_id": r["agent_id"],
                    "level": r["level"],
                    "event_type": r["event_type"],
                    "message": r["message"],
                    "details": json.loads(r["details_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
