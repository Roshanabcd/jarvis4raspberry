"""SQLite (WAL mode) persistence for handwritten-to-text conversion history."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class HandwritingOCRStore:
    """Stores OCR conversions and metadata in SQLite WAL mode."""

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
                CREATE TABLE IF NOT EXISTS ocr_conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    engine_used TEXT NOT NULL,
                    language TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    cleaned_text TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    char_count INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    latency_ms REAL NOT NULL
                );
                """
            )

    def save_conversion(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO ocr_conversions (
                    created_at, filename, width, height, engine_used, language,
                    raw_text, cleaned_text, word_count, char_count, confidence, latency_ms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    rec["filename"],
                    int(rec["width"]),
                    int(rec["height"]),
                    rec["engine_used"],
                    rec["language"],
                    rec["raw_text"],
                    rec["cleaned_text"],
                    int(rec["word_count"]),
                    int(rec["char_count"]),
                    float(rec["confidence"]),
                    float(rec["latency_ms"]),
                ),
            )
            row = conn.execute(
                "SELECT * FROM ocr_conversions WHERE id = ?", (int(cur.lastrowid),)
            ).fetchone()
        return dict(row)

    def get_conversion(self, conversion_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM ocr_conversions WHERE id = ?", (conversion_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_conversions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ocr_conversions ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_conversion(self, conversion_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM ocr_conversions WHERE id = ?", (conversion_id,))
        return cur.rowcount > 0

    def count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM ocr_conversions").fetchone()[0])
