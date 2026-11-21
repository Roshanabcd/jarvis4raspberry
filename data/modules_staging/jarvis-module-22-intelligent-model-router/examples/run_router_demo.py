"""Runnable CLI demonstration for JARVIS Module 22 — Intelligent AI Model Router."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import ModelRouterConfig
from backend.services.router_engine import IntelligentModelRouterEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = ModelRouterConfig(db_path=str(Path(tmp) / "demo_router.db"))
        engine = IntelligentModelRouterEngine(cfg)

        print("1. Auto-classifying & routing a coding prompt (quality_first)...")
        r1 = engine.route_request("Write a Python FastAPI middleware to log latency.", strategy="quality_first")
        print(f"   Task: {r1['routing_decision']['resolved_task_type']} | Selected: {r1['selected_model_id']} | Cost: ${r1['cost_usd']}")

        print("2. Re-sending identical prompt to verify SHA-256 response cache...")
        r2 = engine.route_request("Write a Python FastAPI middleware to log latency.", strategy="quality_first")
        print(f"   Cache hit: {r2['cache_hit']} | Cost: ${r2['cost_usd']} | Latency: {r2['latency_ms']}ms")

        print("3. Simulating outage on primary model and verifying automatic failover...")
        engine.toggle_model(r1["selected_model_id"], simulate_outage=True)
        r3 = engine.route_request("Refactor this SQL query for PostgreSQL indexing.", strategy="quality_first", use_cache=False)
        print(f"   Failover used: {r3['failover_used']} | Fallback model: {r3['selected_model_id']}")

        print("4. Routing with local_only privacy strategy...")
        r4 = engine.route_request("Summarize my private local notes.", strategy="local_only")
        print(f"   Selected local model: {r4['selected_model_id']} | Cost: ${r4['cost_usd']}")

        print("5. Running 3-model side-by-side benchmark...")
        bench = engine.run_benchmark(
            "Compare SQLite WAL and PostgreSQL for Raspberry Pi 5.",
            ["local-llama3-8b", "gemini-2.5-flash", "gpt-4o-mini"],
        )
        print(f"   Benchmark models evaluated: {len(bench['results'])}")
        engine.db.close()
        print("Demo complete.")


if __name__ == "__main__":
    main()
