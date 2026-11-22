"""Isolated SQLite WAL persistence for JARVIS Module 28 — AI Data Analyst."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DataAnalystDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    dataset_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    columns_json TEXT NOT NULL,
                    rows_json TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS query_history (
                    query_id TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    chart_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE CASCADE
                );
                """
            )

    def _row_to_dataset(self, r: sqlite3.Row, include_rows: bool = True) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "dataset_id": r["dataset_id"],
            "name": r["name"],
            "description": r["description"],
            "columns": json.loads(r["columns_json"]),
            "profile": json.loads(r["profile_json"]),
            "row_count": r["row_count"],
            "created_at": r["created_at"],
        }
        if include_rows:
            out["rows"] = json.loads(r["rows_json"])
        return out

    def create_dataset(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO datasets (dataset_id, name, description, columns_json, rows_json, profile_json, row_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["dataset_id"],
                    rec["name"],
                    rec["description"],
                    json.dumps(rec["columns"]),
                    json.dumps(rec["rows"]),
                    json.dumps(rec["profile"]),
                    rec["row_count"],
                    rec["created_at"],
                ),
            )
        return self.get_dataset(rec["dataset_id"])  # type: ignore[return-value]

    def get_dataset(self, dataset_id: str, include_rows: bool = True) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM datasets WHERE dataset_id = ?", (dataset_id,)).fetchone()
            return self._row_to_dataset(row, include_rows=include_rows) if row else None

    def list_datasets(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM datasets ORDER BY created_at DESC").fetchall()
            return [self._row_to_dataset(r, include_rows=False) for r in rows]

    def add_query(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO query_history (query_id, dataset_id, question, answer, chart_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["query_id"],
                    rec["dataset_id"],
                    rec["question"],
                    rec["answer"],
                    json.dumps(rec["chart"]) if rec.get("chart") is not None else None,
                    rec["created_at"],
                ),
            )
        return rec

    def list_queries(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if dataset_id:
                rows = conn.execute("SELECT * FROM query_history WHERE dataset_id = ? ORDER BY created_at DESC", (dataset_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM query_history ORDER BY created_at DESC").fetchall()
            out = []
            for r in rows:
                out.append(
                    {
                        "query_id": r["query_id"],
                        "dataset_id": r["dataset_id"],
                        "question": r["question"],
                        "answer": r["answer"],
                        "chart": json.loads(r["chart_json"]) if r["chart_json"] else None,
                        "created_at": r["created_at"],
                    }
                )
            return out
