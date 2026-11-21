"""SQLite WAL persistence layer for JARVIS Module 36 — Screen Vision Assistant."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class VisionDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path).expanduser().resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS captures (
                    capture_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    image_format TEXT NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    byte_size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    ocr_text TEXT NOT NULL,
                    elements_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vision_queries (
                    query_id TEXT PRIMARY KEY,
                    capture_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    matched_elements_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (capture_id) REFERENCES captures(capture_id) ON DELETE CASCADE
                );
                """
            )

    @staticmethod
    def _row_to_capture(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "capture_id": row["capture_id"],
            "title": row["title"],
            "source": row["source"],
            "image_format": row["image_format"],
            "width": row["width"],
            "height": row["height"],
            "byte_size": row["byte_size"],
            "sha256": row["sha256"],
            "ocr_text": row["ocr_text"],
            "elements": json.loads(row["elements_json"]),
            "created_at": row["created_at"],
        }

    def add_capture(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO captures (
                    capture_id, title, source, image_format, width, height,
                    byte_size, sha256, ocr_text, elements_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["capture_id"],
                    item["title"],
                    item["source"],
                    item["image_format"],
                    item["width"],
                    item["height"],
                    item["byte_size"],
                    item["sha256"],
                    item["ocr_text"],
                    json.dumps(item["elements"]),
                    item["created_at"],
                ),
            )
        return item

    def get_capture(self, capture_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM captures WHERE capture_id = ?", (capture_id,)).fetchone()
        return self._row_to_capture(row) if row else None

    def list_captures(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM captures ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_capture(r) for r in rows]

    def add_query(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO vision_queries (
                    query_id, capture_id, question, answer, matched_elements_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item["query_id"],
                    item["capture_id"],
                    item["question"],
                    item["answer"],
                    json.dumps(item["matched_elements"]),
                    item["created_at"],
                ),
            )
        return item

    def list_queries(self, capture_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if capture_id:
                rows = conn.execute(
                    "SELECT * FROM vision_queries WHERE capture_id = ? ORDER BY created_at DESC LIMIT ?",
                    (capture_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM vision_queries ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
        return [
            {
                "query_id": r["query_id"],
                "capture_id": r["capture_id"],
                "question": r["question"],
                "answer": r["answer"],
                "matched_elements": json.loads(r["matched_elements_json"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
