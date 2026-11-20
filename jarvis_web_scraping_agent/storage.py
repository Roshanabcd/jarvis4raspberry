"""SQLite (WAL mode) storage for web monitors and extracted HTML snapshots."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class WebScraperStore:
    """Stores monitored URLs, extraction snapshots, and change diffs in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS scrape_monitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    target_tag TEXT,
                    interval_minutes INTEGER NOT NULL,
                    last_checked_at TEXT,
                    last_hash TEXT,
                    last_text TEXT,
                    change_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'active'
                );

                CREATE TABLE IF NOT EXISTS scrape_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    monitor_id INTEGER,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    changed INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (monitor_id) REFERENCES scrape_monitors(id) ON DELETE SET NULL
                );
                """
            )

    def create_monitor(
        self,
        name: str,
        url: str,
        target_tag: Optional[str],
        interval_minutes: int,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO scrape_monitors (created_at, name, url, target_tag, interval_minutes, status)
                VALUES (?, ?, ?, ?, ?, 'active')
                """,
                (now, name, url, target_tag, interval_minutes),
            )
            row = conn.execute("SELECT * FROM scrape_monitors WHERE id = ?", (int(cur.lastrowid),)).fetchone()
        return dict(row)

    def get_monitor(self, monitor_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM scrape_monitors WHERE id = ?", (monitor_id,)).fetchone()
        return dict(row) if row else None

    def list_monitors(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM scrape_monitors ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

    def update_monitor_check(
        self,
        monitor_id: int,
        content_hash: str,
        full_text: str,
        changed: bool,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE scrape_monitors
                SET last_checked_at = ?, last_hash = ?, last_text = ?,
                    change_count = change_count + ?
                WHERE id = ?
                """,
                (now, content_hash, full_text, 1 if changed else 0, monitor_id),
            )

    def save_snapshot(
        self,
        source: str,
        title: str,
        content_hash: str,
        word_count: int,
        payload: Dict[str, Any],
        monitor_id: Optional[int] = None,
        changed: bool = False,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO scrape_snapshots
                    (created_at, monitor_id, source, title, content_hash, word_count, changed, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    monitor_id,
                    source,
                    title[:300],
                    content_hash,
                    word_count,
                    int(changed),
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            return int(cur.lastrowid)

    def list_snapshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, monitor_id, source, title, content_hash, word_count, changed
                FROM scrape_snapshots
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [{**dict(r), "changed": bool(r["changed"])} for r in rows]

    def get_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM scrape_snapshots WHERE id = ?", (snapshot_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["changed"] = bool(d["changed"])
        d["payload"] = json.loads(d.pop("payload_json"))
        return d

    def counts(self) -> Dict[str, int]:
        with self._connect() as conn:
            mons = int(conn.execute("SELECT COUNT(*) FROM scrape_monitors WHERE status = 'active'").fetchone()[0])
            snaps = int(conn.execute("SELECT COUNT(*) FROM scrape_snapshots").fetchone()[0])
        return {"active_monitors": mons, "total_snapshots": snaps}
