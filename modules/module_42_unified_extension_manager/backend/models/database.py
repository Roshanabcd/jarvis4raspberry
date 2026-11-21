"""SQLite WAL Module Registry, Scan History, Approvals, Audit Logs, and Event Store (Module 42)."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from typing import Any, Dict, List, Optional

from modules.module_42_unified_extension_manager.sdk.jarvis_sdk.contracts import HealthStatus, utc_now_iso


class ExtensionRegistryDB:
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
            CREATE TABLE IF NOT EXISTS modules (
                module_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'extension',
                source_archive TEXT,
                installed_location TEXT,
                integration_status TEXT NOT NULL DEFAULT 'discovered',
                enabled INTEGER NOT NULL DEFAULT 0,
                health_status TEXT NOT NULL DEFAULT 'not_verified',
                health_endpoint TEXT,
                dependencies_json TEXT NOT NULL DEFAULT '{}',
                required_permissions_json TEXT NOT NULL DEFAULT '[]',
                config_json TEXT NOT NULL DEFAULT '{}',
                compatibility_json TEXT NOT NULL DEFAULT '{}',
                scan_metadata_json TEXT NOT NULL DEFAULT '{}',
                last_verified_at TEXT,
                error_details TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approvals (
                request_id TEXT PRIMARY KEY,
                module_id TEXT NOT NULL,
                action TEXT NOT NULL,
                summary TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                requested_by TEXT NOT NULL,
                reviewer TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id TEXT,
                level TEXT NOT NULL DEFAULT 'INFO',
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS event_history (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                source_module TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                timestamp TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    @staticmethod
    def _row_to_module(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "module_id": row["module_id"],
            "name": row["name"],
            "version": row["version"],
            "category": row["category"],
            "source_archive": row["source_archive"],
            "installed_location": row["installed_location"],
            "integration_status": row["integration_status"],
            "enabled": bool(row["enabled"]),
            "health_status": row["health_status"],
            "health_endpoint": row["health_endpoint"],
            "dependencies": json.loads(row["dependencies_json"]),
            "required_permissions": json.loads(row["required_permissions_json"]),
            "config": json.loads(row["config_json"]),
            "compatibility": json.loads(row["compatibility_json"]),
            "scan_metadata": json.loads(row["scan_metadata_json"]),
            "last_verified_at": row["last_verified_at"],
            "error_details": row["error_details"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def upsert_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        existing = self.get_module(data["module_id"])
        created_at = existing["created_at"] if existing else now
        enabled = int(bool(data.get("enabled", existing["enabled"] if existing else False)))
        health_status = data.get("health_status")
        if not health_status:
            if not enabled:
                health_status = HealthStatus.DISABLED.value if existing else HealthStatus.NOT_VERIFIED.value
            else:
                health_status = existing["health_status"] if existing else HealthStatus.NOT_VERIFIED.value

        with self._lock:
            self._conn.execute(
                """
                INSERT INTO modules (
                    module_id, name, version, category, source_archive, installed_location,
                    integration_status, enabled, health_status, health_endpoint,
                    dependencies_json, required_permissions_json, config_json,
                    compatibility_json, scan_metadata_json, last_verified_at, error_details,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(module_id) DO UPDATE SET
                    name=excluded.name,
                    version=excluded.version,
                    category=excluded.category,
                    source_archive=COALESCE(excluded.source_archive, modules.source_archive),
                    installed_location=COALESCE(excluded.installed_location, modules.installed_location),
                    integration_status=excluded.integration_status,
                    enabled=excluded.enabled,
                    health_status=excluded.health_status,
                    health_endpoint=COALESCE(excluded.health_endpoint, modules.health_endpoint),
                    dependencies_json=excluded.dependencies_json,
                    required_permissions_json=excluded.required_permissions_json,
                    config_json=excluded.config_json,
                    compatibility_json=excluded.compatibility_json,
                    scan_metadata_json=excluded.scan_metadata_json,
                    last_verified_at=COALESCE(excluded.last_verified_at, modules.last_verified_at),
                    error_details=excluded.error_details,
                    updated_at=excluded.updated_at
                """,
                (
                    data["module_id"],
                    data["name"],
                    data.get("version", "0.0.0"),
                    data.get("category", "extension"),
                    data.get("source_archive"),
                    data.get("installed_location"),
                    data.get("integration_status", "discovered"),
                    enabled,
                    health_status,
                    data.get("health_endpoint"),
                    json.dumps(data.get("dependencies", {})),
                    json.dumps(data.get("required_permissions", [])),
                    json.dumps(data.get("config", {})),
                    json.dumps(data.get("compatibility", {})),
                    json.dumps(data.get("scan_metadata", {})),
                    data.get("last_verified_at"),
                    data.get("error_details"),
                    created_at,
                    now,
                ),
            )
            self._conn.commit()
            out = self.get_module(data["module_id"])
            assert out is not None
            return out

    def get_module(self, module_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM modules WHERE module_id = ?", (module_id,)).fetchone()
            return self._row_to_module(row) if row else None

    def list_modules(self, enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if enabled is None:
                rows = self._conn.execute("SELECT * FROM modules ORDER BY module_id ASC").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM modules WHERE enabled = ? ORDER BY module_id ASC", (1 if enabled else 0,)
                ).fetchall()
            return [self._row_to_module(r) for r in rows]

    def set_enabled(self, module_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        existing = self.get_module(module_id)
        if not existing:
            return None
        next_health = HealthStatus.DISABLED.value if not enabled else HealthStatus.NOT_VERIFIED.value
        with self._lock:
            self._conn.execute(
                "UPDATE modules SET enabled = ?, health_status = ?, updated_at = ? WHERE module_id = ?",
                (1 if enabled else 0, next_health, utc_now_iso(), module_id),
            )
            self._conn.commit()
        return self.get_module(module_id)

    def update_config(
        self,
        module_id: str,
        config: Dict[str, Any],
        health_endpoint: Optional[str] = None,
        installed_location: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        existing = self.get_module(module_id)
        if not existing:
            return None
        with self._lock:
            self._conn.execute(
                """
                UPDATE modules
                SET config_json = ?,
                    health_endpoint = COALESCE(?, health_endpoint),
                    installed_location = COALESCE(?, installed_location),
                    updated_at = ?
                WHERE module_id = ?
                """,
                (json.dumps(config), health_endpoint, installed_location, utc_now_iso(), module_id),
            )
            self._conn.commit()
        return self.get_module(module_id)

    def update_health(self, module_id: str, status: str, error_details: Optional[str] = None) -> Optional[Dict[str, Any]]:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                "UPDATE modules SET health_status = ?, last_verified_at = ?, error_details = ?, updated_at = ? WHERE module_id = ?",
                (status, now, error_details, now, module_id),
            )
            self._conn.commit()
        return self.get_module(module_id)

    # --- Approvals ---
    def create_approval(self, module_id: str, action: str, summary: str, requested_by: str) -> Dict[str, Any]:
        req_id = f"apr_{uuid.uuid4().hex[:10]}"
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO approvals (request_id, module_id, action, summary, status, requested_by, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """,
                (req_id, module_id, action, summary, requested_by, now),
            )
            self._conn.commit()
            return self.get_approval(req_id)  # type: ignore[return-value]

    def get_approval(self, request_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM approvals WHERE request_id = ?", (request_id,)).fetchone()
            return dict(row) if row else None

    def list_approvals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute("SELECT * FROM approvals WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM approvals ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def decide_approval(self, request_id: str, status: str, reviewer: str, notes: str = "") -> Optional[Dict[str, Any]]:
        with self._lock:
            self._conn.execute(
                "UPDATE approvals SET status = ?, reviewer = ?, notes = ?, decided_at = ? WHERE request_id = ?",
                (status, reviewer, notes, utc_now_iso(), request_id),
            )
            self._conn.commit()
        return self.get_approval(request_id)

    # --- Audit Logs ---
    def add_log(
        self,
        event_type: str,
        message: str,
        level: str = "INFO",
        module_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO audit_logs (module_id, level, event_type, message, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (module_id, level, event_type, message, json.dumps(details or {}), now),
            )
            self._conn.commit()
            return {
                "log_id": cur.lastrowid,
                "module_id": module_id,
                "level": level,
                "event_type": event_type,
                "message": message,
                "details": details or {},
                "created_at": now,
            }

    def list_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT ?", (limit,)).fetchall()
            return [
                {
                    "log_id": r["log_id"],
                    "module_id": r["module_id"],
                    "level": r["level"],
                    "event_type": r["event_type"],
                    "message": r["message"],
                    "details": json.loads(r["details_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    # --- Event History ---
    def persist_event(self, event_dict: Dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO event_history (event_id, event_type, correlation_id, source_module, payload_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_dict["event_id"],
                    event_dict["event_type"],
                    event_dict["correlation_id"],
                    event_dict["source_module"],
                    json.dumps(event_dict.get("payload", {})),
                    event_dict["timestamp"],
                ),
            )
            self._conn.commit()

    def list_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM event_history ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            return [
                {
                    "event_id": r["event_id"],
                    "event_type": r["event_type"],
                    "correlation_id": r["correlation_id"],
                    "source_module": r["source_module"],
                    "payload": json.loads(r["payload_json"]),
                    "timestamp": r["timestamp"],
                }
                for r in rows
            ]
