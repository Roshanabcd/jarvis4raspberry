"""
JARVIS Long-Term Memory Database
SQLite-backed persistent memory with category support and semantic search hooks.
"""
import sqlite3
import json
import time
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS.Memory.LongTerm")


class MemoryDB:
    """
    Production SQLite memory store for JARVIS.

    Categories: USER, PROJECT, ROBOT, SYSTEM, CONVERSATION, TASK, KNOWLEDGE
    Never stores: API keys, passwords, tokens, private secrets.
    """

    VALID_CATEGORIES = {
        "USER",
        "PROJECT",
        "ROBOT",
        "SYSTEM",
        "CONVERSATION",
        "TASK",
        "KNOWLEDGE",
        "PREFERENCE",
        "EVENT",
    }

    def __init__(self, db_path: str = "jarvis_memory.db") -> None:
        self.db_path = db_path
        self._init_db()
        logger.info(f"MemoryDB initialized at {self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            # Base table — columns added one-by-one for safe migration
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    category    TEXT    NOT NULL,
                    content     TEXT    NOT NULL,
                    created_at  REAL    NOT NULL,
                    updated_at  REAL    NOT NULL
                )
            """)
            # Idempotent column additions (ALTER TABLE IF NOT EXISTS not in SQLite)
            existing = {r[1] for r in conn.execute("PRAGMA table_info(memories)").fetchall()}
            migrations = [
                ("key",          "TEXT"),
                ("tags",         "TEXT    DEFAULT '[]'"),
                ("importance",   "INTEGER DEFAULT 5"),
                ("access_count", "INTEGER DEFAULT 0"),
            ]
            for col, defn in migrations:
                if col not in existing:
                    conn.execute(f"ALTER TABLE memories ADD COLUMN {col} {defn}")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON memories(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON memories(key)")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    query       TEXT    NOT NULL,
                    tool_used   TEXT,
                    result      TEXT,
                    success     INTEGER DEFAULT 1,
                    duration_ms REAL,
                    created_at  REAL    NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT    NOT NULL,
                    request_id  TEXT,
                    message_id  TEXT    UNIQUE NOT NULL,
                    role        TEXT    NOT NULL,
                    content     TEXT    NOT NULL,
                    timestamp   REAL    NOT NULL,
                    provider    TEXT,
                    model       TEXT,
                    tools_used  TEXT    DEFAULT '[]',
                    status      TEXT    DEFAULT 'completed',
                    error       TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON conversation_messages(session_id, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_msg_id ON conversation_messages(message_id)")

    # ------------------------------------------------------------------
    # Persistent Conversation Storage (Phase 1J)
    # ------------------------------------------------------------------

    def save_message(
        self,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tools_used: Optional[List[Any]] = None,
        status: str = "completed",
        error: Optional[str] = None,
    ) -> int:
        """Persist a conversation turn to SQLite."""
        now = time.time()
        tools_json = json.dumps(tools_used or [])
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT OR REPLACE INTO conversation_messages 
                   (session_id, request_id, message_id, role, content, timestamp, provider, model, tools_used, status, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, request_id, message_id, role, content, now, provider, model, tools_json, status, error)
            )
            return cur.lastrowid

    def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve historical turns for a specific session."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT session_id, request_id, message_id, role, content, timestamp, provider, model, tools_used, status, error
                   FROM conversation_messages
                   WHERE session_id = ?
                   ORDER BY timestamp ASC
                   LIMIT ?""",
                (session_id, limit)
            ).fetchall()
            messages = []
            for r in rows:
                tools = []
                try:
                    tools = json.loads(r["tools_used"]) if r["tools_used"] else []
                except Exception:
                    pass
                messages.append({
                    "session_id": r["session_id"],
                    "request_id": r["request_id"],
                    "message_id": r["message_id"],
                    "role": r["role"],
                    "content": r["content"],
                    "timestamp": r["timestamp"],
                    "provider": r["provider"],
                    "model": r["model"],
                    "tools_used": tools,
                    "status": r["status"],
                    "error": r["error"],
                })
            return messages

    def clear_session_messages(self, session_id: str) -> int:
        """Clear all stored messages for a specific session."""
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM conversation_messages WHERE session_id = ?", (session_id,))
            return cur.rowcount

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def store(self, category: str, content: str,
              key: Optional[str] = None,
              tags: Optional[List[str]] = None,
              importance: int = 5) -> int:
        """Store a memory. Returns the new row id."""
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Valid: {self.VALID_CATEGORIES}")
        now = time.time()
        tags_json = json.dumps(tags or [])
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT INTO memories (category, key, content, tags, importance, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (category, key, content, tags_json, importance, now, now)
            )
            row_id = cur.lastrowid
        logger.debug(f"Stored memory id={row_id} category={category}")
        return row_id

    def search(self, query: str = "", category: Optional[str] = None,
               limit: int = 20) -> List[Dict[str, Any]]:
        """
        Basic keyword search over content.
        (Vector/semantic search can be layered on top via memory/vector/)
        """
        sql = "SELECT * FROM memories WHERE 1=1"
        params: list = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        if query:
            sql += " AND content LIKE ?"
            params.append(f"%{query}%")
        sql += " ORDER BY importance DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()
            # Increment access counter
            for row in rows:
                conn.execute(
                    "UPDATE memories SET access_count = access_count + 1 WHERE id = ?",
                    (row["id"],)
                )
        return [dict(r) for r in rows]

    def update(self, memory_id: int, content: str,
               importance: Optional[int] = None) -> bool:
        """Update an existing memory by id."""
        now = time.time()
        fields = ["content = ?", "updated_at = ?"]
        params: list = [content, now]
        if importance is not None:
            fields.append("importance = ?")
            params.append(importance)
        params.append(memory_id)
        with self._get_conn() as conn:
            conn.execute(f"UPDATE memories SET {', '.join(fields)} WHERE id = ?", params)
        logger.debug(f"Updated memory id={memory_id}")
        return True

    def delete(self, memory_id: int) -> bool:
        """Delete a memory by id."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        logger.info(f"Deleted memory id={memory_id}")
        return True

    def retrieve_context(self, category: str = "CONVERSATION",
                         limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent context entries for a given category."""
        return self.search(category=category, limit=limit)

    def summarize(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Return counts and recent entries for inspection."""
        with self._get_conn() as conn:
            if category:
                total = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE category = ?", (category,)
                ).fetchone()[0]
            else:
                total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        return {"total_memories": total, "category": category or "ALL"}

    # ------------------------------------------------------------------
    # Task history
    # ------------------------------------------------------------------

    def log_task(self, query: str, tool_used: str = "",
                 result: str = "", success: bool = True,
                 duration_ms: float = 0.0) -> None:
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO task_history (query, tool_used, result, success, duration_ms, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (query, tool_used, result, int(success), duration_ms, now)
            )

    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM task_history ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


# Module-level singleton — use absolute path so JARVIS works from any CWD
_default_db_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "jarvis_memory.db"
)
_default_db_path = os.path.normpath(_default_db_path)
_db_path = os.environ.get("JARVIS_DB_PATH", _default_db_path)
db = MemoryDB(db_path=_db_path)
