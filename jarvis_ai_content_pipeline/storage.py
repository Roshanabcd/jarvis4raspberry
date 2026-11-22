"""SQLite (WAL mode) persistence for generated content assets and campaigns."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContentPipelineStore:
    """Stores generated blogs, scripts, hooks, carousels, and campaigns in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS content_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    markdown TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_content_items_type_created
                    ON content_items(content_type, created_at DESC);
                """
            )

    def save_item(
        self,
        content_type: str,
        title: str,
        topic: str,
        provider: str,
        markdown: str,
        payload: Dict[str, Any],
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO content_items
                    (created_at, content_type, title, topic, provider, markdown, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    content_type,
                    title[:300],
                    topic[:500],
                    provider,
                    markdown,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            return int(cur.lastrowid)

    def list_items(
        self,
        content_type: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            if content_type:
                rows = conn.execute(
                    """
                    SELECT id, created_at, content_type, title, provider, topic
                    FROM content_items
                    WHERE content_type = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (content_type, safe_limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, created_at, content_type, title, provider, topic
                    FROM content_items
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        return [dict(r) for r in rows]

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, created_at, content_type, title, topic, provider, markdown, payload_json
                FROM content_items
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["payload"] = json.loads(data.pop("payload_json"))
        return data

    def count_items(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM content_items").fetchone()
            return int(row["cnt"]) if row else 0
