"""SQLite (WAL mode) persistence for ROI intrusion zones, detection analytics, and alerts."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class ObjectDetectionStore:
    """Stores ROI zones, frame telemetry, and triggered alerts in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS objdet_zones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    name TEXT NOT NULL UNIQUE,
                    x1 REAL NOT NULL,
                    y1 REAL NOT NULL,
                    x2 REAL NOT NULL,
                    y2 REAL NOT NULL,
                    watch_classes_json TEXT NOT NULL,
                    min_confidence REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS objdet_frames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    stream_id TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    object_count INTEGER NOT NULL,
                    class_counts_json TEXT NOT NULL,
                    latency_ms REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS objdet_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    zone_name TEXT NOT NULL,
                    label TEXT NOT NULL,
                    track_id INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    stream_id TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _hydrate_zone(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["watch_classes"] = json.loads(d.pop("watch_classes_json"))
        return d

    def upsert_zone(
        self,
        name: str,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        watch_classes: List[str],
        min_confidence: float,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO objdet_zones (created_at, name, x1, y1, x2, y2, watch_classes_json, min_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    x1 = excluded.x1,
                    y1 = excluded.y1,
                    x2 = excluded.x2,
                    y2 = excluded.y2,
                    watch_classes_json = excluded.watch_classes_json,
                    min_confidence = excluded.min_confidence
                """,
                (now, name, x1, y1, x2, y2, json.dumps(watch_classes), min_confidence),
            )
            row = conn.execute("SELECT * FROM objdet_zones WHERE name = ?", (name,)).fetchone()
        return self._hydrate_zone(row)

    def list_zones(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM objdet_zones ORDER BY id ASC").fetchall()
        return [self._hydrate_zone(r) for r in rows]

    def delete_zone(self, zone_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM objdet_zones WHERE id = ?", (zone_id,))
        return cur.rowcount > 0

    def log_frame(
        self,
        stream_id: str,
        backend: str,
        object_count: int,
        class_counts: Dict[str, int],
        latency_ms: float,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO objdet_frames (created_at, stream_id, backend, object_count, class_counts_json, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, stream_id, backend, object_count, json.dumps(class_counts), latency_ms),
            )

    def log_alert(
        self,
        zone_name: str,
        label: str,
        track_id: int,
        confidence: float,
        stream_id: str,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO objdet_alerts (created_at, zone_name, label, track_id, confidence, stream_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, zone_name, label, track_id, confidence, stream_id),
            )
            row = conn.execute("SELECT * FROM objdet_alerts WHERE id = ?", (int(cur.lastrowid),)).fetchone()
        return dict(row)

    def list_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM objdet_alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def analytics(self) -> Dict[str, Any]:
        with self._connect() as conn:
            f_row = conn.execute(
                "SELECT COUNT(*) AS cnt, COALESCE(SUM(object_count), 0) AS objs, COALESCE(AVG(latency_ms), 0.0) AS avg_lat FROM objdet_frames"
            ).fetchone()
            total_alerts = int(conn.execute("SELECT COUNT(*) FROM objdet_alerts").fetchone()[0])
            total_zones = int(conn.execute("SELECT COUNT(*) FROM objdet_zones").fetchone()[0])
            cc_rows = conn.execute("SELECT class_counts_json FROM objdet_frames ORDER BY id DESC LIMIT 500").fetchall()
        dist: Dict[str, int] = {}
        for r in cc_rows:
            for k, v in json.loads(r["class_counts_json"]).items():
                dist[k] = dist.get(k, 0) + int(v)
        return {
            "total_zones": total_zones,
            "total_frames_processed": int(f_row["cnt"]),
            "total_detections": int(f_row["objs"]),
            "total_alerts": total_alerts,
            "avg_latency_ms": round(float(f_row["avg_lat"]), 2),
            "class_distribution": dist,
        }
