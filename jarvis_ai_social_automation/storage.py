"""SQLite (WAL mode) storage for social media campaigns, scheduled posts, and engagement metrics."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class SocialAutomationStore:
    """Persists social posts, publishing status, and engagement metrics in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS social_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    campaign_name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    title TEXT NOT NULL,
                    copy_text TEXT NOT NULL,
                    hashtags_json TEXT NOT NULL,
                    scheduled_for TEXT NOT NULL,
                    status TEXT NOT NULL,
                    published_at TEXT,
                    publish_mode TEXT,
                    export_path TEXT,
                    impressions INTEGER NOT NULL DEFAULT 0,
                    likes INTEGER NOT NULL DEFAULT 0,
                    comments INTEGER NOT NULL DEFAULT 0,
                    shares INTEGER NOT NULL DEFAULT 0,
                    clicks INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_social_posts_status_sched
                    ON social_posts(status, scheduled_for);
                """
            )

    @staticmethod
    def _hydrate(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["hashtags"] = json.loads(d.pop("hashtags_json"))
        d["character_count"] = len(d["copy_text"])
        return d

    def create_post(
        self,
        campaign_name: str,
        platform: str,
        title: str,
        copy_text: str,
        hashtags: List[str],
        scheduled_for: str,
        status: str = "scheduled",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO social_posts
                    (created_at, campaign_name, platform, title, copy_text, hashtags_json, scheduled_for, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    campaign_name,
                    platform,
                    title,
                    copy_text,
                    json.dumps(hashtags, ensure_ascii=False),
                    scheduled_for,
                    status,
                ),
            )
            post_id = int(cur.lastrowid)
            row = conn.execute("SELECT * FROM social_posts WHERE id = ?", (post_id,)).fetchone()
        return self._hydrate(row)

    def get_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM social_posts WHERE id = ?", (post_id,)).fetchone()
        return self._hydrate(row) if row else None

    def list_posts(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        clauses: List[str] = []
        params: List[Any] = []
        if platform:
            clauses.append("LOWER(platform) = LOWER(?)")
            params.append(platform)
        if status:
            clauses.append("LOWER(status) = LOWER(?)")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(safe_limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM social_posts {where} ORDER BY scheduled_for ASC, id DESC LIMIT ?",
                params,
            ).fetchall()
        return [self._hydrate(r) for r in rows]

    def list_due_posts(self, now_iso: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM social_posts
                WHERE status = 'scheduled' AND scheduled_for <= ?
                ORDER BY scheduled_for ASC
                """,
                (now_iso,),
            ).fetchall()
        return [self._hydrate(r) for r in rows]

    def mark_published(
        self,
        post_id: int,
        status: str,
        publish_mode: str,
        export_path: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE social_posts
                SET status = ?, published_at = ?, publish_mode = ?, export_path = ?
                WHERE id = ?
                """,
                (status, now if status == "published" else None, publish_mode, export_path, post_id),
            )
            row = conn.execute("SELECT * FROM social_posts WHERE id = ?", (post_id,)).fetchone()
        return self._hydrate(row) if row else None

    def update_metrics(
        self,
        post_id: int,
        impressions: int,
        likes: int,
        comments: int,
        shares: int,
        clicks: int,
    ) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE social_posts
                SET impressions = ?, likes = ?, comments = ?, shares = ?, clicks = ?
                WHERE id = ?
                """,
                (impressions, likes, comments, shares, clicks, post_id),
            )
            row = conn.execute("SELECT * FROM social_posts WHERE id = ?", (post_id,)).fetchone()
        return self._hydrate(row) if row else None

    def count_posts(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM social_posts").fetchone()
            return int(row["cnt"]) if row else 0
