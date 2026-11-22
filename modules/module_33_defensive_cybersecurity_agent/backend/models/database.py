"""SQLite WAL persistence layer for JARVIS Module 33 — Defensive Cybersecurity Agent."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CyberSecurityDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS scan_runs (
                    scan_id TEXT PRIMARY KEY,
                    target_path TEXT NOT NULL,
                    files_scanned INTEGER NOT NULL,
                    findings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS fim_baselines (
                    baseline_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    hashes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    remediation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    resolution_note TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def add_scan_run(self, scan_id: str, target_path: str, files_scanned: int, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO scan_runs (scan_id, target_path, files_scanned, findings_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (scan_id, target_path, files_scanned, json.dumps(findings), now),
            )
        return {
            "scan_id": scan_id,
            "target_path": target_path,
            "files_scanned": files_scanned,
            "findings": findings,
            "findings_count": len(findings),
            "created_at": now,
        }

    def list_scans(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM scan_runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [
                {
                    "scan_id": r["scan_id"],
                    "target_path": r["target_path"],
                    "files_scanned": r["files_scanned"],
                    "findings": json.loads(r["findings_json"]),
                    "findings_count": len(json.loads(r["findings_json"])),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def create_baseline(self, baseline_id: str, name: str, target_path: str, hashes: Dict[str, str]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO fim_baselines (baseline_id, name, target_path, hashes_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (baseline_id, name, target_path, json.dumps(hashes), now),
            )
        return {
            "baseline_id": baseline_id,
            "name": name,
            "target_path": target_path,
            "file_count": len(hashes),
            "created_at": now,
        }

    def get_baseline(self, baseline_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM fim_baselines WHERE baseline_id = ?", (baseline_id,)).fetchone()
            if not row:
                return None
            return {
                "baseline_id": row["baseline_id"],
                "name": row["name"],
                "target_path": row["target_path"],
                "hashes": json.loads(row["hashes_json"]),
                "created_at": row["created_at"],
            }

    def list_baselines(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM fim_baselines ORDER BY created_at DESC").fetchall()
            return [
                {
                    "baseline_id": r["baseline_id"],
                    "name": r["name"],
                    "target_path": r["target_path"],
                    "file_count": len(json.loads(r["hashes_json"])),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def add_incident(self, inc: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO incidents
                (incident_id, category, severity, title, detail, remediation, status, resolution_note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inc["incident_id"],
                    inc["category"],
                    inc["severity"],
                    inc["title"],
                    inc["detail"],
                    inc["remediation"],
                    inc["status"],
                    inc["resolution_note"],
                    inc["created_at"],
                    inc["updated_at"],
                ),
            )
        return inc

    def list_incidents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if status:
                rows = conn.execute("SELECT * FROM incidents WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 100").fetchall()
            return [dict(r) for r in rows]

    def resolve_incident(self, incident_id: str, resolution_note: str) -> Optional[Dict[str, Any]]:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "UPDATE incidents SET status = 'resolved', resolution_note = ?, updated_at = ? WHERE incident_id = ?",
                (resolution_note, now, incident_id),
            )
            row = conn.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)).fetchone()
            return dict(row) if row else None
