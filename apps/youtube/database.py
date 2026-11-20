"""
SQLite Storage Engine for JARVIS YouTube AI.

Tables:
- videos: Cached video metadata (id, title, channel, duration, thumbnail, etc.)
- transcripts: Parsed segments and chunks with user isolation.
- notes: User-saved summaries, chapters, key points, and study notes.
- history: User activity audit log (queries, summaries, exports).
"""
import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional
import uuid

from .models import (
    ChapterSource,
    TranscriptChunk,
    TranscriptSegment,
    TranscriptSource,
    VideoChapter,
    VideoNote,
    YouTubeVideoInfo,
)

logger = logging.getLogger("JARVIS.YouTube.Database")

DEFAULT_DB_PATH = "/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/youtube_notes.sqlite3"


class YouTubeDatabase:
    """
    User-isolated SQLite storage for YouTube video metadata, transcripts,
    notes, and history.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    channel_title TEXT,
                    channel_id TEXT,
                    duration_seconds INTEGER DEFAULT 0,
                    duration_formatted TEXT DEFAULT '00:00',
                    thumbnail_url TEXT,
                    published_at TEXT,
                    description TEXT,
                    captions_available INTEGER DEFAULT 0,
                    metadata_source TEXT DEFAULT 'oembed',
                    embed_permitted INTEGER DEFAULT 1,
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    segments_json TEXT NOT NULL,
                    chunks_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    UNIQUE(video_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS notes (
                    note_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    video_title TEXT NOT NULL,
                    channel TEXT,
                    summary_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    chapters_json TEXT DEFAULT '[]',
                    key_points_json TEXT DEFAULT '[]',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS history (
                    history_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details_json TEXT DEFAULT '{}',
                    timestamp REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id);
                CREATE INDEX IF NOT EXISTS idx_transcripts_user_video ON transcripts(user_id, video_id);
                CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id);
                """
            )

    # ── Videos ─────────────────────────────────────────────────────────────
    def save_video(self, info: YouTubeVideoInfo) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO videos (
                    video_id, url, title, channel_title, channel_id,
                    duration_seconds, duration_formatted, thumbnail_url,
                    published_at, description, captions_available,
                    metadata_source, embed_permitted, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    url=excluded.url,
                    title=excluded.title,
                    channel_title=excluded.channel_title,
                    channel_id=excluded.channel_id,
                    duration_seconds=excluded.duration_seconds,
                    duration_formatted=excluded.duration_formatted,
                    thumbnail_url=excluded.thumbnail_url,
                    published_at=excluded.published_at,
                    description=excluded.description,
                    captions_available=excluded.captions_available,
                    metadata_source=excluded.metadata_source,
                    embed_permitted=excluded.embed_permitted
                """,
                (
                    info.video_id,
                    info.url,
                    info.title,
                    info.channel_title,
                    info.channel_id,
                    info.duration_seconds,
                    info.duration_formatted,
                    info.thumbnail_url,
                    info.published_at,
                    info.description,
                    1 if info.captions_available else 0,
                    info.metadata_source,
                    1 if info.embed_permitted else 0,
                    time.time(),
                ),
            )

    def get_video(self, video_id: str) -> Optional[YouTubeVideoInfo]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM videos WHERE video_id = ?", (video_id,)
            ).fetchone()
            if not row:
                return None
            return YouTubeVideoInfo(
                video_id=row["video_id"],
                url=row["url"],
                title=row["title"],
                channel_title=row["channel_title"] or "Unknown Channel",
                channel_id=row["channel_id"],
                duration_seconds=row["duration_seconds"],
                duration_formatted=row["duration_formatted"],
                thumbnail_url=row["thumbnail_url"] or "",
                published_at=row["published_at"],
                description=row["description"] or "",
                captions_available=bool(row["captions_available"]),
                metadata_source=row["metadata_source"],
                embed_permitted=bool(row["embed_permitted"]),
            )

    # ── Transcripts ────────────────────────────────────────────────────────
    def save_transcript(
        self,
        video_id: str,
        user_id: str,
        source: str,
        language: str,
        segments: List[TranscriptSegment],
        chunks: List[TranscriptChunk],
    ) -> None:
        seg_data = [s.to_dict() for s in segments]
        chunk_data = [c.to_dict() for c in chunks]

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transcripts (
                    video_id, user_id, source, language,
                    segments_json, chunks_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id, user_id) DO UPDATE SET
                    source=excluded.source,
                    language=excluded.language,
                    segments_json=excluded.segments_json,
                    chunks_json=excluded.chunks_json,
                    created_at=excluded.created_at
                """,
                (
                    video_id,
                    user_id,
                    source,
                    language,
                    json.dumps(seg_data),
                    json.dumps(chunk_data),
                    time.time(),
                ),
            )

    def get_transcript(
        self, video_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM transcripts WHERE video_id = ? AND user_id = ?",
                (video_id, user_id),
            ).fetchone()
            if not row:
                return None

            raw_segs = json.loads(row["segments_json"])
            raw_chunks = json.loads(row["chunks_json"])

            segments = [
                TranscriptSegment(
                    segment_id=s["segment_id"],
                    start=s["start"],
                    end=s["end"],
                    text=s["text"],
                    speaker=s.get("speaker"),
                    source=TranscriptSource(s["source"]) if s.get("source") in TranscriptSource._value2member_map_ else TranscriptSource.USER_UPLOADED_TXT,
                    language=s.get("language", "en"),
                    confidence=s.get("confidence"),
                )
                for s in raw_segs
            ]

            chunks = [
                TranscriptChunk(
                    chunk_id=c["chunk_id"],
                    video_id=c["video_id"],
                    user_id=c["user_id"],
                    chunk_index=c["chunk_index"],
                    start=c["start"],
                    end=c["end"],
                    text=c["text"],
                    source=c["source"],
                    speaker=c.get("speaker"),
                    start_formatted=c.get("start_formatted", ""),
                    end_formatted=c.get("end_formatted", ""),
                )
                for c in raw_chunks
            ]

            return {
                "video_id": video_id,
                "user_id": user_id,
                "source": row["source"],
                "language": row["language"],
                "segments": segments,
                "chunks": chunks,
                "created_at": row["created_at"],
            }

    # ── Notes & Summaries ──────────────────────────────────────────────────
    def save_note(self, note: VideoNote) -> VideoNote:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO notes (
                    note_id, user_id, video_id, video_title, channel,
                    summary_type, content, chapters_json, key_points_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(note_id) DO UPDATE SET
                    summary_type=excluded.summary_type,
                    content=excluded.content,
                    chapters_json=excluded.chapters_json,
                    key_points_json=excluded.key_points_json,
                    updated_at=excluded.updated_at
                """,
                (
                    note.note_id,
                    note.user_id,
                    note.video_id,
                    note.video_title,
                    note.channel,
                    note.summary_type,
                    note.content,
                    json.dumps(note.chapters),
                    json.dumps(note.key_points),
                    note.created_at,
                    note.updated_at,
                ),
            )
        return note

    def get_note(self, note_id: str, user_id: str) -> Optional[VideoNote]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE note_id = ? AND user_id = ?",
                (note_id, user_id),
            ).fetchone()
            if not row:
                return None
            return VideoNote(
                note_id=row["note_id"],
                user_id=row["user_id"],
                video_id=row["video_id"],
                video_title=row["video_title"],
                channel=row["channel"] or "",
                summary_type=row["summary_type"],
                content=row["content"],
                chapters=json.loads(row["chapters_json"] or "[]"),
                key_points=json.loads(row["key_points_json"] or "[]"),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_notes(
        self, user_id: str, query: str = "", limit: int = 50
    ) -> List[VideoNote]:
        with self._get_connection() as conn:
            if query.strip():
                wildcard = f"%{query.strip()}%"
                rows = conn.execute(
                    """
                    SELECT * FROM notes
                    WHERE user_id = ? AND (video_title LIKE ? OR content LIKE ? OR channel LIKE ?)
                    ORDER BY updated_at DESC LIMIT ?
                    """,
                    (user_id, wildcard, wildcard, wildcard, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM notes
                    WHERE user_id = ?
                    ORDER BY updated_at DESC LIMIT ?
                    """,
                    (user_id, limit),
                ).fetchall()

            return [
                VideoNote(
                    note_id=row["note_id"],
                    user_id=row["user_id"],
                    video_id=row["video_id"],
                    video_title=row["video_title"],
                    channel=row["channel"] or "",
                    summary_type=row["summary_type"],
                    content=row["content"],
                    chapters=json.loads(row["chapters_json"] or "[]"),
                    key_points=json.loads(row["key_points_json"] or "[]"),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def delete_note(self, note_id: str, user_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM notes WHERE note_id = ? AND user_id = ?",
                (note_id, user_id),
            )
            return cur.rowcount > 0

    def export_note(
        self, note_id: str, user_id: str, export_format: str = "markdown"
    ) -> str:
        note = self.get_note(note_id, user_id)
        if not note:
            raise KeyError(f"Note '{note_id}' not found for user '{user_id}'.")

        fmt = export_format.lower()
        if fmt == "json":
            return json.dumps(note.to_dict(), indent=2)

        elif fmt == "text":
            lines = [
                f"VIDEO TITLE: {note.video_title}",
                f"CHANNEL: {note.channel}",
                f"SUMMARY TYPE: {note.summary_type}",
                f"SAVED: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(note.created_at))}",
                "-" * 40,
                "",
                note.content,
                "",
            ]
            if note.key_points:
                lines.append("KEY POINTS:")
                for p in note.key_points:
                    lines.append(f"- {p}")
                lines.append("")
            if note.chapters:
                lines.append("CHAPTERS:")
                for c in note.chapters:
                    lines.append(f"[{c.get('start_formatted', '00:00')}] {c.get('title', '')}")
                lines.append("")
            return "\n".join(lines)

        else:
            # Markdown format default
            md = [
                f"# {note.video_title}",
                f"**Channel:** {note.channel} | **Type:** {note.summary_type}",
                f"*Saved on {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(note.created_at))}*",
                "",
                "---",
                "",
                note.content,
                "",
            ]
            if note.key_points:
                md.append("## Key Takeaways")
                for p in note.key_points:
                    md.append(f"- {p}")
                md.append("")
            if note.chapters:
                md.append("## Chapters")
                for c in note.chapters:
                    ts = c.get("start_formatted", "00:00")
                    link = c.get("youtube_url", "#")
                    title = c.get("title", "")
                    md.append(f"- [{ts}]({link}) **{title}**")
                md.append("")
            return "\n".join(md)

    # ── History ────────────────────────────────────────────────────────────
    def record_history(
        self,
        user_id: str,
        video_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO history (history_id, user_id, video_id, action, details_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"hist_{uuid.uuid4().hex[:10]}",
                    user_id,
                    video_id,
                    action,
                    json.dumps(details or {}),
                    time.time(),
                ),
            )

    def get_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT h.*, v.title as video_title, v.thumbnail_url, v.channel_title
                FROM history h
                LEFT JOIN videos v ON h.video_id = v.video_id
                WHERE h.user_id = ?
                ORDER BY h.timestamp DESC LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

            return [
                {
                    "history_id": row["history_id"],
                    "user_id": row["user_id"],
                    "video_id": row["video_id"],
                    "video_title": row["video_title"] or "YouTube Video",
                    "channel_title": row["channel_title"] or "",
                    "thumbnail_url": row["thumbnail_url"] or "",
                    "action": row["action"],
                    "details": json.loads(row["details_json"] or "{}"),
                    "timestamp": row["timestamp"],
                    "timestamp_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row["timestamp"])),
                }
                for row in rows
            ]

    def clear_history(self, user_id: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
            return True
