"""SQLite WAL persistence layer for JARVIS Module 22 — Intelligent AI Model Router."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ModelRouterDB:
    def __init__(self, db_path: str) -> None:
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA foreign_keys=ON;")
            self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS models (
                model_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                display_name TEXT NOT NULL,
                capabilities_json TEXT NOT NULL,
                cost_per_1k_input_usd REAL NOT NULL,
                cost_per_1k_output_usd REAL NOT NULL,
                avg_latency_ms INTEGER NOT NULL,
                quality_score REAL NOT NULL,
                max_context_tokens INTEGER NOT NULL,
                privacy_tier TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                simulate_outage INTEGER NOT NULL DEFAULT 0,
                circuit_state TEXT NOT NULL DEFAULT 'closed',
                failure_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS routing_logs (
                request_id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                strategy TEXT NOT NULL,
                selected_model_id TEXT NOT NULL,
                failover_used INTEGER NOT NULL DEFAULT 0,
                cache_hit INTEGER NOT NULL DEFAULT 0,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                latency_ms INTEGER NOT NULL,
                status TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS response_cache (
                cache_key TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                response_text TEXT NOT NULL,
                task_type TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS router_policy (
                policy_key TEXT PRIMARY KEY,
                policy_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # --- Models ---
    def _row_to_model(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "model_id": r["model_id"],
            "provider": r["provider"],
            "display_name": r["display_name"],
            "capabilities": json.loads(r["capabilities_json"]),
            "cost_per_1k_input_usd": r["cost_per_1k_input_usd"],
            "cost_per_1k_output_usd": r["cost_per_1k_output_usd"],
            "avg_latency_ms": r["avg_latency_ms"],
            "quality_score": r["quality_score"],
            "max_context_tokens": r["max_context_tokens"],
            "privacy_tier": r["privacy_tier"],
            "enabled": bool(r["enabled"]),
            "simulate_outage": bool(r["simulate_outage"]),
            "circuit_state": r["circuit_state"],
            "failure_count": r["failure_count"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }

    def upsert_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO models (
                    model_id, provider, display_name, capabilities_json,
                    cost_per_1k_input_usd, cost_per_1k_output_usd, avg_latency_ms,
                    quality_score, max_context_tokens, privacy_tier,
                    enabled, simulate_outage, circuit_state, failure_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_id) DO UPDATE SET
                    provider=excluded.provider,
                    display_name=excluded.display_name,
                    capabilities_json=excluded.capabilities_json,
                    cost_per_1k_input_usd=excluded.cost_per_1k_input_usd,
                    cost_per_1k_output_usd=excluded.cost_per_1k_output_usd,
                    avg_latency_ms=excluded.avg_latency_ms,
                    quality_score=excluded.quality_score,
                    max_context_tokens=excluded.max_context_tokens,
                    privacy_tier=excluded.privacy_tier,
                    enabled=excluded.enabled,
                    updated_at=excluded.updated_at
                """,
                (
                    data["model_id"],
                    data["provider"],
                    data["display_name"],
                    json.dumps(data.get("capabilities", ["general"])),
                    float(data.get("cost_per_1k_input_usd", 0.0)),
                    float(data.get("cost_per_1k_output_usd", 0.0)),
                    int(data.get("avg_latency_ms", 350)),
                    float(data.get("quality_score", 0.8)),
                    int(data.get("max_context_tokens", 32768)),
                    data.get("privacy_tier", "cloud"),
                    1 if data.get("enabled", True) else 0,
                    1 if data.get("simulate_outage", False) else 0,
                    data.get("circuit_state", "closed"),
                    int(data.get("failure_count", 0)),
                    data.get("created_at", now),
                    now,
                ),
            )
            self._conn.commit()
        return self.get_model(data["model_id"])  # type: ignore[return-value]

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM models WHERE model_id=?", (model_id,)).fetchone()
            return self._row_to_model(row) if row else None

    def list_models(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM models ORDER BY privacy_tier DESC, quality_score DESC").fetchall()
            return [self._row_to_model(r) for r in rows]

    def update_model_state(
        self,
        model_id: str,
        *,
        enabled: Optional[bool] = None,
        simulate_outage: Optional[bool] = None,
        circuit_state: Optional[str] = None,
        failure_count: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        cur = self.get_model(model_id)
        if not cur:
            return None
        with self._lock:
            self._conn.execute(
                """
                UPDATE models SET
                    enabled=?, simulate_outage=?, circuit_state=?, failure_count=?, updated_at=?
                WHERE model_id=?
                """,
                (
                    1 if (cur["enabled"] if enabled is None else enabled) else 0,
                    1 if (cur["simulate_outage"] if simulate_outage is None else simulate_outage) else 0,
                    cur["circuit_state"] if circuit_state is None else circuit_state,
                    cur["failure_count"] if failure_count is None else failure_count,
                    utc_now_iso(),
                    model_id,
                ),
            )
            self._conn.commit()
        return self.get_model(model_id)

    # --- Routing Logs & Spend ---
    def record_routing_log(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO routing_logs (
                    request_id, task_type, strategy, selected_model_id,
                    failover_used, cache_hit, input_tokens, output_tokens,
                    cost_usd, latency_ms, status, decision_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["request_id"],
                    entry["task_type"],
                    entry["strategy"],
                    entry["selected_model_id"],
                    1 if entry.get("failover_used") else 0,
                    1 if entry.get("cache_hit") else 0,
                    int(entry["input_tokens"]),
                    int(entry["output_tokens"]),
                    float(entry["cost_usd"]),
                    int(entry["latency_ms"]),
                    entry["status"],
                    json.dumps(entry.get("decision", {})),
                    entry["created_at"],
                ),
            )
            self._conn.commit()
        return entry

    def list_routing_logs(self, limit: int = 80) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM routing_logs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            out = []
            for r in rows:
                out.append(
                    {
                        "request_id": r["request_id"],
                        "task_type": r["task_type"],
                        "strategy": r["strategy"],
                        "selected_model_id": r["selected_model_id"],
                        "failover_used": bool(r["failover_used"]),
                        "cache_hit": bool(r["cache_hit"]),
                        "input_tokens": r["input_tokens"],
                        "output_tokens": r["output_tokens"],
                        "cost_usd": r["cost_usd"],
                        "latency_ms": r["latency_ms"],
                        "status": r["status"],
                        "decision": json.loads(r["decision_json"]),
                        "created_at": r["created_at"],
                    }
                )
            return out

    def get_spend_summary(self) -> Dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT
                    COUNT(*) AS total_requests,
                    COALESCE(SUM(cost_usd), 0.0) AS total_cost_usd,
                    COALESCE(SUM(input_tokens), 0) AS total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
                    COALESCE(SUM(cache_hit), 0) AS cache_hits,
                    COALESCE(SUM(failover_used), 0) AS failovers
                FROM routing_logs
                """
            ).fetchone()
            return {
                "total_requests": int(row["total_requests"]),
                "total_cost_usd": round(float(row["total_cost_usd"]), 6),
                "total_input_tokens": int(row["total_input_tokens"]),
                "total_output_tokens": int(row["total_output_tokens"]),
                "cache_hits": int(row["cache_hits"]),
                "failovers": int(row["failovers"]),
            }

    # --- Response Cache ---
    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM response_cache WHERE cache_key=?", (cache_key,)).fetchone()
            if not row:
                return None
            return {
                "cache_key": row["cache_key"],
                "model_id": row["model_id"],
                "response_text": row["response_text"],
                "task_type": row["task_type"],
                "created_at": row["created_at"],
            }

    def set_cached_response(self, cache_key: str, model_id: str, response_text: str, task_type: str) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO response_cache (cache_key, model_id, response_text, task_type, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (cache_key, model_id, response_text, task_type, utc_now_iso()),
            )
            self._conn.commit()

    def clear_cache(self) -> int:
        with self._lock:
            cur = self._conn.execute("DELETE FROM response_cache")
            self._conn.commit()
            return cur.rowcount

    # --- Policy ---
    def get_policy_raw(self, key: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute("SELECT policy_json FROM router_policy WHERE policy_key=?", (key,)).fetchone()
            return row["policy_json"] if row else None

    def set_policy_raw(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO router_policy (policy_key, policy_json, updated_at) VALUES (?, ?, ?)",
                (key, value, utc_now_iso()),
            )
            self._conn.commit()
