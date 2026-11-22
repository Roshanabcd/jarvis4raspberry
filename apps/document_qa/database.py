"""
SQLite WAL Database Layer for JARVIS Document AI with Multi-Tenant User Isolation.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional
import uuid

from .models import DocumentChunk, DocumentCollection, DocumentMetadata, DocumentType

logger = logging.getLogger("JARVIS.DocumentAI.Database")

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "document_qa.sqlite3",
)


class DocumentDatabase:
    """Manages SQLite tables for documents, chunks, collections, and conversation history."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        """Create tables if they do not exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    page_count INTEGER,
                    word_count INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    collection TEXT NOT NULL DEFAULT 'default',
                    is_indexed INTEGER NOT NULL DEFAULT 1,
                    storage_path TEXT NOT NULL,
                    title TEXT,
                    author TEXT,
                    metadata_json TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_user ON documents(user_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_collection ON documents(collection);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    page_number INTEGER,
                    section_heading TEXT,
                    text TEXT NOT NULL,
                    char_start INTEGER NOT NULL,
                    char_end INTEGER NOT NULL,
                    word_count INTEGER NOT NULL,
                    FOREIGN KEY(doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON document_chunks(doc_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_user ON document_chunks(user_id);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    collection_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at REAL NOT NULL,
                    UNIQUE(user_id, name)
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS qa_history (
                    query_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    grounded INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    citations_json TEXT,
                    doc_ids_json TEXT,
                    created_at REAL NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_user ON qa_history(user_id);")

    def save_document(self, meta: DocumentMetadata) -> DocumentMetadata:
        """Insert or replace document metadata."""
        with self._get_connection() as conn:
            if meta.collection:
                coll_id = f"coll_{meta.user_id}_{re.sub(r'[^a-zA-Z0-9_]', '_', meta.collection.lower())}"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO collections (collection_id, user_id, name, description, created_at)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (coll_id, meta.user_id, meta.collection, "", time.time()),
                )

            conn.execute(
                """
                INSERT OR REPLACE INTO documents (
                    doc_id, filename, file_type, file_size_bytes, user_id,
                    created_at, updated_at, page_count, word_count, checksum,
                    collection, is_indexed, storage_path, title, author, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    meta.doc_id,
                    meta.filename,
                    meta.file_type.value if hasattr(meta.file_type, "value") else str(meta.file_type),
                    meta.file_size_bytes,
                    meta.user_id,
                    meta.created_at,
                    meta.updated_at,
                    meta.page_count,
                    meta.word_count,
                    meta.checksum,
                    meta.collection,
                    1 if meta.is_indexed else 0,
                    meta.storage_path,
                    meta.title,
                    meta.author,
                    json.dumps(meta.metadata_json),
                ),
            )
        return meta

    def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Batch insert document chunks."""
        if not chunks:
            return
        records = [
            (
                c.chunk_id,
                c.doc_id,
                c.user_id,
                c.chunk_index,
                c.page_number,
                c.section_heading,
                c.text,
                c.char_start,
                c.char_end,
                c.word_count,
            )
            for c in chunks
        ]
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO document_chunks (
                    chunk_id, doc_id, user_id, chunk_index, page_number,
                    section_heading, text, char_start, char_end, word_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                records,
            )

    def get_document(self, doc_id: str, user_id: str) -> Optional[DocumentMetadata]:
        """Fetch a specific document belonging to user."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE doc_id = ? AND user_id = ?;", (doc_id, user_id)
            ).fetchone()
            if not row:
                return None
            return self._row_to_doc(row)

    def list_documents(
        self, user_id: str, collection: Optional[str] = None
    ) -> List[DocumentMetadata]:
        """List documents owned by user, optionally filtered by collection."""
        with self._get_connection() as conn:
            if collection:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE user_id = ? AND collection = ? ORDER BY created_at DESC;",
                    (user_id, collection),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC;",
                    (user_id,),
                ).fetchall()
            return [self._row_to_doc(r) for r in rows]

    def get_document_chunks(self, doc_id: str, user_id: str) -> List[DocumentChunk]:
        """Retrieve all chunks belonging to a document."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM document_chunks WHERE doc_id = ? AND user_id = ? ORDER BY chunk_index ASC;",
                (doc_id, user_id),
            ).fetchall()
            return [self._row_to_chunk(r) for r in rows]

    def delete_document(self, doc_id: str, user_id: str) -> Optional[str]:
        """Delete a document and return its file storage_path for deletion."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT storage_path FROM documents WHERE doc_id = ? AND user_id = ?;",
                (doc_id, user_id),
            ).fetchone()
            if not row:
                return None
            path = row["storage_path"]
            conn.execute("DELETE FROM document_chunks WHERE doc_id = ?;", (doc_id,))
            conn.execute("DELETE FROM documents WHERE doc_id = ? AND user_id = ?;", (doc_id, user_id))
            return path

    def list_collections(self, user_id: str) -> List[DocumentCollection]:
        """List user collections with document counts."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT c.collection_id, c.user_id, c.name, c.description, c.created_at,
                       COUNT(d.doc_id) as doc_count
                FROM collections c
                LEFT JOIN documents d ON c.user_id = d.user_id AND c.name = d.collection
                WHERE c.user_id = ?
                GROUP BY c.collection_id
                ORDER BY c.name ASC;
                """,
                (user_id,),
            ).fetchall()
            return [
                DocumentCollection(
                    collection_id=r["collection_id"],
                    user_id=r["user_id"],
                    name=r["name"],
                    description=r["description"] or "",
                    doc_count=r["doc_count"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def create_collection(
        self, user_id: str, name: str, description: str = ""
    ) -> DocumentCollection:
        """Create a new collection for user."""
        col_id = f"col_{uuid.uuid4().hex[:8]}"
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO collections (collection_id, user_id, name, description, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (col_id, user_id, name.strip(), description.strip(), now),
            )
        return DocumentCollection(
            collection_id=col_id,
            user_id=user_id,
            name=name.strip(),
            description=description.strip(),
            doc_count=0,
            created_at=now,
        )

    def save_qa_record(
        self,
        user_id: str,
        question: str,
        answer: str,
        grounded: bool,
        confidence: float,
        citations: List[Any],
        doc_ids: List[str],
    ) -> None:
        """Record Q&A dialogue turn for history tracking."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO qa_history (
                    query_id, user_id, question, answer, grounded, confidence,
                    citations_json, doc_ids_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    f"qa_{uuid.uuid4().hex[:10]}",
                    user_id,
                    question,
                    answer,
                    1 if grounded else 0,
                    confidence,
                    json.dumps([c.model_dump() if hasattr(c, "model_dump") else str(c) for c in citations]),
                    json.dumps(doc_ids),
                    time.time(),
                ),
            )

    def load_all_chunks(self) -> List[DocumentChunk]:
        """Load all chunks for in-memory index warm-up on boot."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM document_chunks ORDER BY chunk_index ASC;").fetchall()
            return [self._row_to_chunk(r) for r in rows]

    def _row_to_doc(self, r: sqlite3.Row) -> DocumentMetadata:
        meta_json = {}
        if r["metadata_json"]:
            try:
                meta_json = json.loads(r["metadata_json"])
            except Exception:
                pass
        return DocumentMetadata(
            doc_id=r["doc_id"],
            filename=r["filename"],
            file_type=DocumentType(r["file_type"]) if r["file_type"] in DocumentType.__members__.values() else DocumentType.UNKNOWN,
            file_size_bytes=r["file_size_bytes"],
            user_id=r["user_id"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            page_count=r["page_count"],
            word_count=r["word_count"],
            checksum=r["checksum"],
            collection=r["collection"],
            is_indexed=bool(r["is_indexed"]),
            storage_path=r["storage_path"],
            title=r["title"],
            author=r["author"],
            metadata_json=meta_json,
        )

    def _row_to_chunk(self, r: sqlite3.Row) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=r["chunk_id"],
            doc_id=r["doc_id"],
            user_id=r["user_id"],
            chunk_index=r["chunk_index"],
            page_number=r["page_number"],
            section_heading=r["section_heading"],
            text=r["text"],
            char_start=r["char_start"],
            char_end=r["char_end"],
            word_count=r["word_count"],
        )


db = DocumentDatabase()
