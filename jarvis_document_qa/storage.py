"""SQLite (WAL mode) persistence for indexed documents and embedded chunks."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class DocumentStore:
    """Stores documents, chunk text, and 128-D embeddings in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS docqa_documents (
                    doc_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    tags_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS docqa_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    section TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    FOREIGN KEY (doc_id) REFERENCES docqa_documents(doc_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_docqa_chunks_doc
                    ON docqa_chunks(doc_id);
                """
            )

    @staticmethod
    def _hydrate_doc(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["tags"] = json.loads(d.pop("tags_json"))
        return d

    def save_document_with_chunks(
        self,
        doc_id: str,
        title: str,
        filename: str,
        doc_type: str,
        char_count: int,
        tags: List[str],
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("DELETE FROM docqa_documents WHERE doc_id = ?", (doc_id,))
            conn.execute(
                """
                INSERT INTO docqa_documents
                    (doc_id, created_at, title, filename, doc_type, char_count, chunk_count, tags_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    now,
                    title,
                    filename,
                    doc_type,
                    char_count,
                    len(chunks),
                    json.dumps(tags, ensure_ascii=False),
                ),
            )
            conn.executemany(
                """
                INSERT INTO docqa_chunks (doc_id, chunk_index, section, content, embedding_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        doc_id,
                        int(ch["chunk_index"]),
                        str(ch["section"]),
                        str(ch["content"]),
                        json.dumps(ch["embedding"]),
                    )
                    for ch in chunks
                ],
            )
            row = conn.execute(
                "SELECT * FROM docqa_documents WHERE doc_id = ?", (doc_id,)
            ).fetchone()
        return self._hydrate_doc(row)

    def list_documents(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM docqa_documents ORDER BY created_at DESC"
            ).fetchall()
        return [self._hydrate_doc(r) for r in rows]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM docqa_documents WHERE doc_id = ?", (doc_id,)
            ).fetchone()
        return self._hydrate_doc(row) if row else None

    def delete_document(self, doc_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM docqa_documents WHERE doc_id = ?", (doc_id,))
        return cur.rowcount > 0

    def list_chunks(self, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if doc_id:
                rows = conn.execute(
                    """
                    SELECT c.doc_id, c.chunk_index, c.section, c.content, c.embedding_json,
                           d.title AS doc_title, d.filename AS filename
                    FROM docqa_chunks c
                    JOIN docqa_documents d ON d.doc_id = c.doc_id
                    WHERE c.doc_id = ?
                    ORDER BY c.chunk_index ASC
                    """,
                    (doc_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT c.doc_id, c.chunk_index, c.section, c.content, c.embedding_json,
                           d.title AS doc_title, d.filename AS filename
                    FROM docqa_chunks c
                    JOIN docqa_documents d ON d.doc_id = c.doc_id
                    ORDER BY c.id ASC
                    """
                ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            d["embedding"] = json.loads(d.pop("embedding_json"))
            out.append(d)
        return out

    def counts(self) -> Dict[str, int]:
        with self._connect() as conn:
            docs = int(conn.execute("SELECT COUNT(*) FROM docqa_documents").fetchone()[0])
            chunks = int(conn.execute("SELECT COUNT(*) FROM docqa_chunks").fetchone()[0])
        return {"total_documents": docs, "total_chunks": chunks}
