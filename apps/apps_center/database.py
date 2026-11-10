"""
JARVIS OS — Shared Database and Storage Foundation for Apps Center.
Manages schema migrations, user-isolated application storage, favorites,
recent applications, audit events, and background task records in jarvis_memory.db.
"""

import json
import logging
import os
import shutil
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.AppsCenter.Database")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "jarvis_memory.db"
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class AppsCenterDatabase:
    """Thread-safe SQLite storage manager for Apps Center entities."""
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppsCenterDatabase, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[Path] = None):
        if self._initialized:
            return
        with self._lock:
            self._db_path = db_path or DB_PATH
            self._init_tables()
            self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def backup_database(self) -> str:
        """Create a timestamped backup before migrations or destructive operations."""
        ts = int(time.time())
        dest = BACKUP_DIR / f"jarvis_memory_backup_{ts}.db"
        if self._db_path.exists():
            shutil.copy2(self._db_path, dest)
            logger.info("Database backed up to: %s", dest)
            return str(dest)
        return ""

    def _init_tables(self) -> None:
        """Initialize all Apps Center tables with indexes and constraints."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()

                # 1. Applications table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS applications (
                        id                  TEXT PRIMARY KEY,
                        name                TEXT NOT NULL,
                        category            TEXT NOT NULL,
                        status              TEXT NOT NULL,
                        enabled             INTEGER DEFAULT 1,
                        launch_count        INTEGER DEFAULT 0,
                        last_launched_at    REAL,
                        created_at          REAL NOT NULL,
                        updated_at          REAL NOT NULL
                    );
                """)

                # 2. Application settings (user-isolated)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS application_settings (
                        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_id              TEXT NOT NULL,
                        user_id             TEXT NOT NULL,
                        setting_key         TEXT NOT NULL,
                        setting_value       TEXT NOT NULL,
                        is_encrypted        INTEGER DEFAULT 0,
                        updated_at          REAL NOT NULL,
                        UNIQUE(app_id, user_id, setting_key)
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_app_settings_user ON application_settings(app_id, user_id);")

                # 3. User favorites (per user)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_favorites (
                        user_id             TEXT NOT NULL,
                        app_id              TEXT NOT NULL,
                        created_at          REAL NOT NULL,
                        PRIMARY KEY(user_id, app_id)
                    );
                """)

                # 4. Recently opened apps
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS recently_opened_apps (
                        user_id             TEXT NOT NULL,
                        app_id              TEXT NOT NULL,
                        opened_at           REAL NOT NULL,
                        PRIMARY KEY(user_id, app_id)
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_recent_user_opened ON recently_opened_apps(user_id, opened_at DESC);")

                # 5. Application usage telemetry
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS app_usage_events (
                        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_id              TEXT NOT NULL,
                        user_id             TEXT NOT NULL,
                        event_type          TEXT NOT NULL,
                        duration_s          REAL DEFAULT 0.0,
                        metadata_json       TEXT DEFAULT '{}',
                        timestamp           REAL NOT NULL
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_time ON app_usage_events(app_id, timestamp DESC);")

                # 6. Provider configurations
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS provider_configurations (
                        provider_name       TEXT PRIMARY KEY,
                        is_enabled          INTEGER DEFAULT 1,
                        model_name          TEXT NOT NULL,
                        base_url            TEXT,
                        is_healthy          INTEGER DEFAULT 0,
                        last_tested_at      REAL,
                        error_message       TEXT,
                        updated_at          REAL NOT NULL
                    );
                """)

                # 7. App permissions
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS app_permissions (
                        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_id              TEXT NOT NULL,
                        role                TEXT NOT NULL,
                        permission_token    TEXT NOT NULL,
                        is_granted          INTEGER DEFAULT 1,
                        UNIQUE(app_id, role, permission_token)
                    );
                """)

                # 8. Background application tasks
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS app_tasks (
                        task_id             TEXT PRIMARY KEY,
                        app_id              TEXT NOT NULL,
                        user_id             TEXT NOT NULL,
                        task_type           TEXT NOT NULL,
                        status              TEXT NOT NULL,
                        progress_pct        INTEGER DEFAULT 0,
                        message             TEXT,
                        payload_json        TEXT DEFAULT '{}',
                        result_json         TEXT DEFAULT '{}',
                        error               TEXT,
                        created_at          REAL NOT NULL,
                        started_at          REAL,
                        completed_at        REAL
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_app_tasks_user ON app_tasks(user_id, status);")

                conn.commit()
                logger.info("✓ Apps Center database tables verified in %s", self._db_path)
            except Exception as e:
                logger.error("Database migration error: %s", e)
                conn.rollback()
            finally:
                conn.close()

    # ── User Favorites ──────────────────────────────────────
    def toggle_favorite(self, user_id: str, app_id: str) -> bool:
        """Toggle favorite state for a specific user and application."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM user_favorites WHERE user_id = ? AND app_id = ?;", (user_id, app_id))
                exists = cur.fetchone() is not None
                if exists:
                    cur.execute("DELETE FROM user_favorites WHERE user_id = ? AND app_id = ?;", (user_id, app_id))
                    is_fav = False
                else:
                    cur.execute(
                        "INSERT INTO user_favorites (user_id, app_id, created_at) VALUES (?, ?, ?);",
                        (user_id, app_id, time.time()),
                    )
                    is_fav = True
                conn.commit()
                return is_fav
            finally:
                conn.close()

    def get_user_favorites(self, user_id: str) -> List[str]:
        """Return list of favorite app IDs for the specified user."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("SELECT app_id FROM user_favorites WHERE user_id = ? ORDER BY created_at DESC;", (user_id,))
                return [row["app_id"] for row in cur.fetchall()]
            finally:
                conn.close()

    # ── Recently Opened Apps ────────────────────────────────
    def record_app_opened(self, user_id: str, app_id: str) -> None:
        """Record an app launch for recent list and global stats."""
        now = time.time()
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                # Upsert recently opened
                cur.execute("""
                    INSERT INTO recently_opened_apps (user_id, app_id, opened_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, app_id) DO UPDATE SET opened_at = excluded.opened_at;
                """, (user_id, app_id, now))

                # Track usage event
                cur.execute("""
                    INSERT INTO app_usage_events (app_id, user_id, event_type, duration_s, timestamp)
                    VALUES (?, ?, 'launch', 0.0, ?);
                """, (app_id, user_id, now))

                # Increment launch count in applications table
                cur.execute("""
                    INSERT INTO applications (id, name, category, status, enabled, launch_count, last_launched_at, created_at, updated_at)
                    VALUES (?, ?, 'general', 'active', 1, 1, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        launch_count = launch_count + 1,
                        last_launched_at = excluded.last_launched_at,
                        updated_at = excluded.updated_at;
                """, (app_id, app_id, now, now, now))

                conn.commit()
            finally:
                conn.close()

    def get_recently_opened(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recently opened app IDs with timestamps for a user."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT app_id, opened_at FROM recently_opened_apps
                    WHERE user_id = ?
                    ORDER BY opened_at DESC LIMIT ?;
                """, (user_id, limit))
                return [{"app_id": row["app_id"], "opened_at": row["opened_at"]} for row in cur.fetchall()]
            finally:
                conn.close()

    # ── Application Settings (User-Isolated) ─────────────────
    def set_app_setting(self, app_id: str, user_id: str, key: str, value: Any, is_encrypted: bool = False) -> None:
        """Store user-isolated application setting."""
        val_str = json.dumps(value) if not isinstance(value, str) else value
        now = time.time()
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO application_settings (app_id, user_id, setting_key, setting_value, is_encrypted, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(app_id, user_id, setting_key) DO UPDATE SET
                        setting_value = excluded.setting_value,
                        is_encrypted = excluded.is_encrypted,
                        updated_at = excluded.updated_at;
                """, (app_id, user_id, key, val_str, int(is_encrypted), now))
                conn.commit()
            finally:
                conn.close()

    def get_app_settings(self, app_id: str, user_id: str) -> Dict[str, Any]:
        """Fetch all settings for a specific user and application."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT setting_key, setting_value FROM application_settings
                    WHERE app_id = ? AND user_id = ?;
                """, (app_id, user_id))
                out = {}
                for row in cur.fetchall():
                    k, v = row["setting_key"], row["setting_value"]
                    try:
                        out[k] = json.loads(v)
                    except Exception:
                        out[k] = v
                return out
            finally:
                conn.close()

    # ── Task Storage (User-Isolated) ─────────────────────────
    def save_task(self, task: Dict[str, Any]) -> None:
        """Insert or update a background application task."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO app_tasks (
                        task_id, app_id, user_id, task_type, status, progress_pct,
                        message, payload_json, result_json, error, created_at, started_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id) DO UPDATE SET
                        status = excluded.status,
                        progress_pct = excluded.progress_pct,
                        message = excluded.message,
                        result_json = excluded.result_json,
                        error = excluded.error,
                        started_at = excluded.started_at,
                        completed_at = excluded.completed_at;
                """, (
                    task["task_id"],
                    task["app_id"],
                    task["user_id"],
                    task["task_type"],
                    task["status"],
                    task.get("progress_pct", 0),
                    task.get("message"),
                    json.dumps(task.get("payload_json", {})),
                    json.dumps(task.get("result_json", {})),
                    task.get("error"),
                    task.get("created_at", time.time()),
                    task.get("started_at"),
                    task.get("completed_at"),
                ))
                conn.commit()
            finally:
                conn.close()

    def get_task(self, task_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve task by ID, enforcing user isolation unless admin check."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                if user_id:
                    cur.execute("SELECT * FROM app_tasks WHERE task_id = ? AND user_id = ?;", (task_id, user_id))
                else:
                    cur.execute("SELECT * FROM app_tasks WHERE task_id = ?;", (task_id,))
                row = cur.fetchone()
                if not row:
                    return None
                d = dict(row)
                try:
                    d["payload_json"] = json.loads(d.get("payload_json") or "{}")
                    d["result_json"] = json.loads(d.get("result_json") or "{}")
                except Exception:
                    pass
                return d
            finally:
                conn.close()

    def list_tasks_for_user(self, user_id: str, app_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List tasks owned by a user, optionally filtered by application."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                if app_id:
                    cur.execute("""
                        SELECT * FROM app_tasks
                        WHERE user_id = ? AND app_id = ?
                        ORDER BY created_at DESC LIMIT ?;
                    """, (user_id, app_id, limit))
                else:
                    cur.execute("""
                        SELECT * FROM app_tasks
                        WHERE user_id = ?
                        ORDER BY created_at DESC LIMIT ?;
                    """, (user_id, limit))
                rows = cur.fetchall()
                out = []
                for r in rows:
                    d = dict(r)
                    try:
                        d["payload_json"] = json.loads(d.get("payload_json") or "{}")
                        d["result_json"] = json.loads(d.get("result_json") or "{}")
                    except Exception:
                        pass
                    out.append(d)
                return out
            finally:
                conn.close()


# Global singleton instance
apps_db = AppsCenterDatabase()
