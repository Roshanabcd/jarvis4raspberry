"""SQLite WAL persistence layer for JARVIS Module 38 — Plugin & Skills Marketplace."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class MarketplaceDB:
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
                CREATE TABLE IF NOT EXISTS packages (
                    package_id TEXT PRIMARY KEY,
                    slug TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    author TEXT NOT NULL,
                    description TEXT NOT NULL,
                    permissions_json TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(slug, version)
                );

                CREATE TABLE IF NOT EXISTS installations (
                    package_id TEXT PRIMARY KEY,
                    enabled INTEGER NOT NULL,
                    installed_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (package_id) REFERENCES packages(package_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS marketplace_audit (
                    event_id TEXT PRIMARY KEY,
                    package_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _row_to_pkg(row: sqlite3.Row, inst: Optional[sqlite3.Row]) -> Dict[str, Any]:
        return {
            "package_id": row["package_id"],
            "slug": row["slug"],
            "name": row["name"],
            "version": row["version"],
            "kind": row["kind"],
            "author": row["author"],
            "description": row["description"],
            "permissions": json.loads(row["permissions_json"]),
            "sha256": row["sha256"],
            "installed": inst is not None,
            "enabled": bool(inst["enabled"]) if inst is not None else False,
            "created_at": row["created_at"],
        }

    def add_package(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO packages (
                    package_id, slug, name, version, kind, author,
                    description, permissions_json, sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["package_id"],
                    item["slug"],
                    item["name"],
                    item["version"],
                    item["kind"],
                    item["author"],
                    item["description"],
                    json.dumps(item["permissions"]),
                    item["sha256"],
                    item["created_at"],
                ),
            )
        return self.get_package(item["package_id"])  # type: ignore[return-value]

    def get_package(self, package_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM packages WHERE package_id = ?", (package_id,)).fetchone()
            if not row:
                return None
            inst = conn.execute("SELECT * FROM installations WHERE package_id = ?", (package_id,)).fetchone()
        return self._row_to_pkg(row, inst)

    def get_by_slug_version(self, slug: str, version: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM packages WHERE slug = ? AND version = ?", (slug, version)).fetchone()
            if not row:
                return None
            inst = conn.execute("SELECT * FROM installations WHERE package_id = ?", (row["package_id"],)).fetchone()
        return self._row_to_pkg(row, inst)

    def list_packages(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM packages ORDER BY created_at DESC").fetchall()
            inst_map = {
                r["package_id"]: r for r in conn.execute("SELECT * FROM installations").fetchall()
            }
        items = [self._row_to_pkg(r, inst_map.get(r["package_id"])) for r in rows]
        if query:
            q = query.strip().lower()
            items = [
                p for p in items
                if q in p["slug"].lower() or q in p["name"].lower() or q in p["description"].lower()
            ]
        return items

    def upsert_installation(self, package_id: str, enabled: bool, now: str) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO installations (package_id, enabled, installed_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(package_id) DO UPDATE SET enabled = excluded.enabled, updated_at = excluded.updated_at
                """,
                (package_id, 1 if enabled else 0, now, now),
            )
        return self.get_package(package_id)  # type: ignore[return-value]

    def remove_installation(self, package_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM installations WHERE package_id = ?", (package_id,))
        return cur.rowcount > 0

    def add_audit(self, event: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO marketplace_audit (event_id, package_id, action, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event["event_id"], event["package_id"], event["action"], event["details"], event["created_at"]),
            )
        return event

    def list_audit(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM marketplace_audit ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
