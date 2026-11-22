"""SQLite (WAL mode) persistence for catalog items, dense embeddings, and user interactions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class RecommendationStore:
    """Stores catalog items, 128-D embeddings, and user-item interactions in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS rec_items (
                    item_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    embedding_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rec_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    weight REAL NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES rec_items(item_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_rec_interactions_user
                    ON rec_interactions(user_id);
                """
            )

    @staticmethod
    def _hydrate_item(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["tags"] = json.loads(d.pop("tags_json"))
        d["embedding"] = json.loads(d.pop("embedding_json"))
        return d

    def upsert_item(
        self,
        item_id: str,
        title: str,
        category: str,
        description: str,
        tags: List[str],
        embedding: List[float],
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rec_items (item_id, created_at, title, category, description, tags_json, embedding_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    title=excluded.title,
                    category=excluded.category,
                    description=excluded.description,
                    tags_json=excluded.tags_json,
                    embedding_json=excluded.embedding_json
                """,
                (
                    item_id,
                    now,
                    title,
                    category,
                    description,
                    json.dumps(tags, ensure_ascii=False),
                    json.dumps(embedding),
                ),
            )
            row = conn.execute("SELECT * FROM rec_items WHERE item_id = ?", (item_id,)).fetchone()
        return self._hydrate_item(row)

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM rec_items WHERE item_id = ?", (item_id,)).fetchone()
        return self._hydrate_item(row) if row else None

    def list_items(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM rec_items ORDER BY created_at DESC").fetchall()
        return [self._hydrate_item(r) for r in rows]

    def record_interaction(
        self,
        user_id: str,
        item_id: str,
        event_type: str,
        weight: float,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO rec_interactions (created_at, user_id, item_id, event_type, weight)
                VALUES (?, ?, ?, ?, ?)
                """,
                (now, user_id, item_id, event_type, weight),
            )
            row = conn.execute("SELECT * FROM rec_interactions WHERE id = ?", (int(cur.lastrowid),)).fetchone()
        return dict(row)

    def list_all_interactions(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM rec_interactions ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]

    def counts(self) -> Dict[str, int]:
        with self._connect() as conn:
            items = int(conn.execute("SELECT COUNT(*) FROM rec_items").fetchone()[0])
            inter = int(conn.execute("SELECT COUNT(*) FROM rec_interactions").fetchone()[0])
        return {"total_items": items, "total_interactions": inter}
