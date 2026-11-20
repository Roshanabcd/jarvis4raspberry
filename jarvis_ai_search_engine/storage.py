"""SQLite (WAL mode) storage for multi-source chunks, embeddings, and query history."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class SearchIndexStore:
    """Persists indexed sources, embedded chunks, and search analytics in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS search_items (
                    item_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_uri TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    char_count INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS search_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    location TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES search_items(item_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_search_chunks_item
                    ON search_chunks(item_id);

                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    query TEXT NOT NULL,
                    source_filter TEXT NOT NULL,
                    result_count INTEGER NOT NULL,
                    latency_ms REAL NOT NULL
                );
                """
            )

    @staticmethod
    def _hydrate_source(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["tags"] = json.loads(d.pop("tags_json"))
        return d

    def upsert_source(
        self,
        item_id: str,
        source_type: str,
        title: str,
        source_uri: str,
        tags: List[str],
        char_count: int,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("DELETE FROM search_items WHERE item_id = ?", (item_id,))
            conn.execute(
                """
                INSERT INTO search_items
                    (item_id, created_at, source_type, title, source_uri, tags_json, chunk_count, char_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    now,
                    source_type,
                    title,
                    source_uri,
                    json.dumps(tags, ensure_ascii=False),
                    len(chunks),
                    char_count,
                ),
            )
            conn.executemany(
                """
                INSERT INTO search_chunks (item_id, chunk_index, location, content, embedding_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item_id,
                        int(ch["chunk_index"]),
                        str(ch["location"]),
                        str(ch["content"]),
                        json.dumps(ch["embedding"]),
                    )
                    for ch in chunks
                ],
            )
            row = conn.execute(
                "SELECT * FROM search_items WHERE item_id = ?", (item_id,)
            ).fetchone()
        return self._hydrate_source(row)

    def list_sources(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM search_items ORDER BY created_at DESC"
            ).fetchall()
        return [self._hydrate_source(r) for r in rows]

    def delete_source(self, item_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM search_items WHERE item_id = ?", (item_id,))
        return cur.rowcount > 0

    def list_chunks(self, source_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if source_types:
                placeholders = ",".join("?" for _ in source_types)
                rows = conn.execute(
                    f"""
                    SELECT c.item_id, c.chunk_index, c.location, c.content, c.embedding_json,
                           s.source_type, s.title, s.source_uri, s.tags_json
                    FROM search_chunks c
                    JOIN search_items s ON s.item_id = c.item_id
                    WHERE s.source_type IN ({placeholders})
                    ORDER BY c.id ASC
                    """,
                    tuple(source_types),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT c.item_id, c.chunk_index, c.location, c.content, c.embedding_json,
                           s.source_type, s.title, s.source_uri, s.tags_json
                    FROM search_chunks c
                    JOIN search_items s ON s.item_id = c.item_id
                    ORDER BY c.id ASC
                    """
                ).fetchall()

        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            d["embedding"] = json.loads(d.pop("embedding_json"))
            d["tags"] = json.loads(d.pop("tags_json"))
            out.append(d)
        return out

    def log_query(self, query: str, source_filter: str, result_count: int, latency_ms: float) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO search_history (created_at, query, source_filter, result_count, latency_ms)
                VALUES (?, ?, ?, ?, ?)
                """,
                (now, query, source_filter, result_count, round(latency_ms, 2)),
            )

    def list_history(self, limit: int = 25) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM search_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> Dict[str, Any]:
        with self._connect() as conn:
            total_sources = int(conn.execute("SELECT COUNT(*) FROM search_items").fetchone()[0])
            total_chunks = int(conn.execute("SELECT COUNT(*) FROM search_chunks").fetchone()[0])
            type_rows = conn.execute(
                "SELECT source_type, COUNT(*) AS cnt FROM search_items GROUP BY source_type"
            ).fetchall()
        by_type = {str(r["source_type"]): int(r["cnt"]) for r in type_rows}
        return {
            "total_sources": total_sources,
            "total_chunks": total_chunks,
            "by_source_type": by_type,
        }
