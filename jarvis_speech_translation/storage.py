"""SQLite (WAL mode) persistence for bilingual sessions, transcripts, and custom glossaries."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class SpeechTranslationStore:
    """Stores bilingual sessions, translated utterances, and custom glossary terms in SQLite WAL."""

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
                CREATE TABLE IF NOT EXISTS st_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    lang_a TEXT NOT NULL,
                    lang_b TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS st_utterances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    source_lang TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES st_sessions(session_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_st_utterances_session
                    ON st_utterances(session_id, id ASC);

                CREATE TABLE IF NOT EXISTS st_glossary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    source_term TEXT NOT NULL,
                    target_term TEXT NOT NULL,
                    UNIQUE(source_lang, target_lang, source_term)
                );
                """
            )

    def create_session(self, session_id: str, title: str, lang_a: str, lang_b: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO st_sessions (session_id, created_at, title, lang_a, lang_b)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, now, title, lang_a, lang_b),
            )
            row = conn.execute("SELECT * FROM st_sessions WHERE session_id = ?", (session_id,)).fetchone()
        d = dict(row)
        d["utterances"] = []
        return d

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            srow = conn.execute("SELECT * FROM st_sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not srow:
                return None
            urows = conn.execute(
                "SELECT * FROM st_utterances WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
        d = dict(srow)
        d["utterances"] = [dict(u) for u in urows]
        return d

    def append_utterance(
        self,
        session_id: str,
        speaker: str,
        source_lang: str,
        target_lang: str,
        source_text: str,
        translated_text: str,
        provider: str,
        latency_ms: float,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO st_utterances
                    (session_id, created_at, speaker, source_lang, target_lang,
                     source_text, translated_text, provider, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    now,
                    speaker,
                    source_lang,
                    target_lang,
                    source_text,
                    translated_text,
                    provider,
                    latency_ms,
                ),
            )
            return int(cur.lastrowid)

    def upsert_glossary(
        self,
        source_lang: str,
        target_lang: str,
        source_term: str,
        target_term: str,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO st_glossary (source_lang, target_lang, source_term, target_term)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source_lang, target_lang, source_term) DO UPDATE SET
                    target_term = excluded.target_term
                """,
                (source_lang, target_lang, source_term, target_term),
            )
            row = conn.execute(
                """
                SELECT * FROM st_glossary
                WHERE source_lang = ? AND target_lang = ? AND source_term = ?
                """,
                (source_lang, target_lang, source_term),
            ).fetchone()
        return dict(row)

    def list_glossary(
        self,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if source_lang and target_lang:
                rows = conn.execute(
                    """
                    SELECT * FROM st_glossary
                    WHERE source_lang = ? AND target_lang = ?
                    ORDER BY LENGTH(source_term) DESC
                    """,
                    (source_lang, target_lang),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM st_glossary ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

    def counts(self) -> Dict[str, int]:
        with self._connect() as conn:
            sessions = int(conn.execute("SELECT COUNT(*) FROM st_sessions").fetchone()[0])
            utterances = int(conn.execute("SELECT COUNT(*) FROM st_utterances").fetchone()[0])
        return {"total_sessions": sessions, "total_utterances": utterances}
