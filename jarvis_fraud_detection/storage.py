"""SQLite (WAL mode) storage for security events, anomaly baselines, and fraud alerts."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class FraudStore:
    """Persists scored events and triage alerts in SQLite WAL mode."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS fraud_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    stream_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    amount REAL,
                    ip_address TEXT,
                    geo_country TEXT,
                    device_id TEXT,
                    metadata_json TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    severity TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    signals_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_fraud_events_actor
                    ON fraud_events(actor_id, id DESC);

                CREATE TABLE IF NOT EXISTS fraud_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    event_id INTEGER NOT NULL,
                    stream_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    severity TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    status TEXT NOT NULL,
                    analyst_note TEXT NOT NULL,
                    signals_json TEXT NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES fraud_events(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_fraud_alerts_status
                    ON fraud_alerts(status, id DESC);
                """
            )

    @staticmethod
    def _hydrate_event(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d.pop("metadata_json", None)
        d["signals"] = json.loads(d.pop("signals_json"))
        return d

    @staticmethod
    def _hydrate_alert(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["signals"] = json.loads(d.pop("signals_json"))
        return d

    def get_actor_history(self, actor_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM fraud_events
                WHERE actor_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (actor_id, limit),
            ).fetchall()
        return [self._hydrate_event(r) for r in rows]

    def insert_event_and_optional_alert(
        self,
        event_data: Dict[str, Any],
        create_alert: bool,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO fraud_events (
                    created_at, event_time, stream_type, actor_id, action, status,
                    amount, ip_address, geo_country, device_id, metadata_json,
                    risk_score, severity, decision, signals_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    event_data["event_time"],
                    event_data["stream_type"],
                    event_data["actor_id"],
                    event_data["action"],
                    event_data["status"],
                    event_data["amount"],
                    event_data["ip_address"],
                    event_data["geo_country"],
                    event_data["device_id"],
                    json.dumps(event_data["metadata"], ensure_ascii=False),
                    event_data["risk_score"],
                    event_data["severity"],
                    event_data["decision"],
                    json.dumps(event_data["signals"], ensure_ascii=False),
                ),
            )
            event_id = int(cur.lastrowid)
            alert_id: Optional[int] = None
            if create_alert:
                acur = conn.execute(
                    """
                    INSERT INTO fraud_alerts (
                        created_at, updated_at, event_id, stream_type, actor_id,
                        risk_score, severity, decision, status, analyst_note, signals_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', '', ?)
                    """,
                    (
                        now,
                        now,
                        event_id,
                        event_data["stream_type"],
                        event_data["actor_id"],
                        event_data["risk_score"],
                        event_data["severity"],
                        event_data["decision"],
                        json.dumps(event_data["signals"], ensure_ascii=False),
                    ),
                )
                alert_id = int(acur.lastrowid)
            row = conn.execute("SELECT * FROM fraud_events WHERE id = ?", (event_id,)).fetchone()
        hydrated = self._hydrate_event(row)
        hydrated["alert_id"] = alert_id
        return hydrated

    def list_events(self, limit: int = 50, stream_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if stream_type:
                rows = conn.execute(
                    """
                    SELECT e.*, a.id AS alert_id
                    FROM fraud_events e
                    LEFT JOIN fraud_alerts a ON a.event_id = e.id
                    WHERE e.stream_type = ?
                    ORDER BY e.id DESC LIMIT ?
                    """,
                    (stream_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT e.*, a.id AS alert_id
                    FROM fraud_events e
                    LEFT JOIN fraud_alerts a ON a.event_id = e.id
                    ORDER BY e.id DESC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [self._hydrate_event(r) for r in rows]

    def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM fraud_alerts {where} ORDER BY id DESC LIMIT ?",
                tuple(params),
            ).fetchall()
        return [self._hydrate_alert(r) for r in rows]

    def update_alert(self, alert_id: int, status: str, analyst_note: str) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE fraud_alerts
                SET status = ?, analyst_note = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, analyst_note, now, alert_id),
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM fraud_alerts WHERE id = ?", (alert_id,)).fetchone()
        return self._hydrate_alert(row)

    def summary(self) -> Dict[str, Any]:
        with self._connect() as conn:
            total_events = int(conn.execute("SELECT COUNT(*) FROM fraud_events").fetchone()[0])
            total_alerts = int(conn.execute("SELECT COUNT(*) FROM fraud_alerts").fetchone()[0])
            open_alerts = int(
                conn.execute("SELECT COUNT(*) FROM fraud_alerts WHERE status = 'open'").fetchone()[0]
            )
            by_stream = {
                str(r["stream_type"]): int(r["cnt"])
                for r in conn.execute(
                    "SELECT stream_type, COUNT(*) AS cnt FROM fraud_events GROUP BY stream_type"
                ).fetchall()
            }
            by_sev = {
                str(r["severity"]): int(r["cnt"])
                for r in conn.execute(
                    "SELECT severity, COUNT(*) AS cnt FROM fraud_events GROUP BY severity"
                ).fetchall()
            }
            top_actors = [
                {
                    "actor_id": str(r["actor_id"]),
                    "event_count": int(r["cnt"]),
                    "avg_risk_score": round(float(r["avg_risk"]), 2),
                    "max_risk_score": round(float(r["max_risk"]), 2),
                }
                for r in conn.execute(
                    """
                    SELECT actor_id, COUNT(*) AS cnt, AVG(risk_score) AS avg_risk, MAX(risk_score) AS max_risk
                    FROM fraud_events
                    GROUP BY actor_id
                    ORDER BY max_risk DESC, avg_risk DESC
                    LIMIT 10
                    """
                ).fetchall()
            ]
        return {
            "total_events": total_events,
            "total_alerts": total_alerts,
            "open_alerts": open_alerts,
            "by_stream_type": by_stream,
            "by_severity": by_sev,
            "top_risky_actors": top_actors,
        }
