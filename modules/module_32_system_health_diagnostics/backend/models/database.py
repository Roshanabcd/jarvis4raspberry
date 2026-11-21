"""SQLite WAL persistence layer for JARVIS Module 32 — System Health & Diagnostics."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SystemHealthDB:
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
                CREATE TABLE IF NOT EXISTS metric_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    metrics_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alert_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    metric_key TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    severity TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    metric_key TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    severity TEXT NOT NULL,
                    acknowledged INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS service_checks (
                    service_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    last_status TEXT NOT NULL,
                    last_latency_ms REAL,
                    last_checked_at TEXT
                );
                CREATE TABLE IF NOT EXISTS diagnostic_runs (
                    run_id TEXT PRIMARY KEY,
                    health_score INTEGER NOT NULL,
                    summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def add_snapshot(self, snapshot_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO metric_snapshots (snapshot_id, metrics_json, created_at) VALUES (?, ?, ?)",
                (snapshot_id, json.dumps(metrics), now),
            )
        return {"snapshot_id": snapshot_id, "metrics": metrics, "created_at": now}

    def list_snapshots(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM metric_snapshots ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                {"snapshot_id": r["snapshot_id"], "metrics": json.loads(r["metrics_json"]), "created_at": r["created_at"]}
                for r in rows
            ]

    def create_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO alert_rules (rule_id, name, metric_key, operator, threshold, severity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule["rule_id"],
                    rule["name"],
                    rule["metric_key"],
                    rule["operator"],
                    rule["threshold"],
                    rule["severity"],
                    rule["created_at"],
                ),
            )
        return rule

    def list_rules(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM alert_rules ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def add_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO alerts (alert_id, rule_id, rule_name, metric_key, metric_value, threshold, severity, acknowledged, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert["alert_id"],
                    alert["rule_id"],
                    alert["rule_name"],
                    alert["metric_key"],
                    alert["metric_value"],
                    alert["threshold"],
                    alert["severity"],
                    0,
                    alert["created_at"],
                ),
            )
        return alert

    def list_alerts(self, unacknowledged_only: bool = False) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if unacknowledged_only:
                rows = conn.execute("SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY created_at DESC").fetchall()
            else:
                rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50").fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["acknowledged"] = bool(d["acknowledged"])
                out.append(d)
            return out

    def ack_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.execute("UPDATE alerts SET acknowledged = 1 WHERE alert_id = ?", (alert_id,))
            row = conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["acknowledged"] = bool(d["acknowledged"])
            return d

    def create_service(self, svc: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO service_checks (service_id, name, host, port, last_status, last_latency_ms, last_checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (svc["service_id"], svc["name"], svc["host"], svc["port"], "unknown", None, None),
            )
        return svc

    def update_service_probe(self, service_id: str, status: str, latency_ms: Optional[float]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "UPDATE service_checks SET last_status = ?, last_latency_ms = ?, last_checked_at = ? WHERE service_id = ?",
                (status, latency_ms, now, service_id),
            )
            row = conn.execute("SELECT * FROM service_checks WHERE service_id = ?", (service_id,)).fetchone()
            return dict(row)

    def list_services(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM service_checks ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]

    def add_diagnostic_run(self, run_id: str, health_score: int, summary: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO diagnostic_runs (run_id, health_score, summary_json, created_at) VALUES (?, ?, ?, ?)",
                (run_id, health_score, json.dumps(summary), now),
            )
        return {"run_id": run_id, "health_score": health_score, "summary": summary, "created_at": now}

    def list_diagnostic_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM diagnostic_runs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                {"run_id": r["run_id"], "health_score": r["health_score"], "summary": json.loads(r["summary_json"]), "created_at": r["created_at"]}
                for r in rows
            ]
