"""Unit tests for JARVIS Module 22 — IntelligentModelRouterEngine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from modules.module_22_intelligent_model_router.backend.app.config import ModelRouterConfig
from modules.module_22_intelligent_model_router.backend.services.router_engine import IntelligentModelRouterEngine, classify_task


class TestModelRouterEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.cfg = ModelRouterConfig(
            db_path=str(Path(self._tmp.name) / "test_m22.db"),
            circuit_breaker_threshold=2,
        )
        self.engine = IntelligentModelRouterEngine(self.cfg)

    def tearDown(self) -> None:
        self.engine.db.close()
        self._tmp.cleanup()

    def test_task_classification(self) -> None:
        self.assertEqual(classify_task("Refactor this Python FastAPI bug"), "coding")
        self.assertEqual(classify_task("Summarize these bullet points"), "summarization")
        self.assertEqual(classify_task("Analyze the architecture tradeoffs"), "reasoning")
        self.assertEqual(classify_task("Extract text from this screenshot diagram"), "vision")
        self.assertEqual(classify_task("Hello JARVIS!"), "general")

    def test_routing_strategies_and_local_privacy(self) -> None:
        local_res = self.engine.route_request("Write Python code for a parser", strategy="local_only")
        self.assertTrue(local_res["selected_model_id"].startswith("local-"))
        self.assertEqual(local_res["cost_usd"], 0.0)

        qual_res = self.engine.route_request("Analyze quantum cryptography tradeoffs", strategy="quality_first")
        self.assertEqual(qual_res["selected_model_id"], "gemini-2.5-pro")

    def test_deterministic_cache_hit(self) -> None:
        r1 = self.engine.route_request("Summarize SQLite WAL benefits", strategy="balanced")
        self.assertFalse(r1["cache_hit"])
        r2 = self.engine.route_request("Summarize SQLite WAL benefits", strategy="balanced")
        self.assertTrue(r2["cache_hit"])
        self.assertEqual(r2["cost_usd"], 0.0)

    def test_failover_and_circuit_breaker_trip(self) -> None:
        # Force outage on gemini-2.5-pro (top quality_first model)
        self.engine.toggle_model("gemini-2.5-pro", simulate_outage=True)

        # First call fails over to next model (failure_count=1, circuit still closed)
        r1 = self.engine.route_request("Analyze distributed consensus", strategy="quality_first", use_cache=False)
        self.assertTrue(r1["failover_used"])
        self.assertNotEqual(r1["selected_model_id"], "gemini-2.5-pro")
        m1 = self.engine.db.get_model("gemini-2.5-pro")
        self.assertEqual(m1["failure_count"], 1)
        self.assertEqual(m1["circuit_state"], "closed")

        # Second call trips circuit breaker (failure_count=2 -> open)
        r2 = self.engine.route_request("Compare Raft vs Paxos", strategy="quality_first", use_cache=False)
        self.assertTrue(r2["failover_used"])
        m2 = self.engine.db.get_model("gemini-2.5-pro")
        self.assertEqual(m2["circuit_state"], "open")

        # Reset circuit recovers model
        recovered = self.engine.toggle_model("gemini-2.5-pro", simulate_outage=False, reset_circuit=True)
        self.assertEqual(recovered["circuit_state"], "closed")
        self.assertEqual(recovered["failure_count"], 0)

    def test_budget_cap_downgrades_to_local_model(self) -> None:
        self.engine.update_budget_policy({"daily_budget_usd": 0.0, "downgrade_to_local_on_cap": True})
        res = self.engine.route_request("Analyze complex system architecture", strategy="quality_first", use_cache=False)
        self.assertTrue(res["routing_decision"]["budget_exceeded"])
        self.assertTrue(res["routing_decision"]["local_enforced"])
        self.assertTrue(res["selected_model_id"].startswith("local-"))

    def test_benchmark_multi_model(self) -> None:
        bench = self.engine.run_benchmark(
            "Write a Python binary search.",
            ["local-qwen25-coder", "gemini-2.5-flash", "nonexistent-model"],
        )
        self.assertEqual(len(bench["results"]), 3)
        self.assertEqual(bench["results"][0]["status"], "ok")
        self.assertEqual(bench["results"][2]["status"], "not_found")


if __name__ == "__main__":
    unittest.main()
