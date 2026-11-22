"""FastAPI REST & WebSocket API tests for JARVIS Module 22."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import ModelRouterConfig
from backend.app.main import create_app


class TestModelRouterAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ModelRouterConfig(db_path=str(Path(self._tmp.name) / "api_m22.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.model_router.db.close()
        self._tmp.cleanup()

    def test_health_manifest_status_and_ui(self) -> None:
        h = self.client.get("/api/v1/model-router/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-22-intelligent-model-router")
        self.assertTrue(h.json()["simulated"])

        m = self.client.get("/api/v1/model-router/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["module_number"], 22)

        ui = self.client.get("/model-router")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("INTELLIGENT AI MODEL ROUTER", ui.text)

    def test_route_register_toggle_benchmark_and_cache(self) -> None:
        # Register custom model
        reg = self.client.post(
            "/api/v1/model-router/models",
            json={
                "model_id": "local-phi4-mini",
                "provider": "ollama_local",
                "display_name": "Phi-4 Mini (Local)",
                "capabilities": ["general", "fast"],
                "privacy_tier": "local",
                "avg_latency_ms": 140,
                "quality_score": 0.76,
            },
        )
        self.assertEqual(reg.status_code, 201)

        # Route prompt
        r = self.client.post(
            "/api/v1/model-router/route",
            json={"prompt": "Write a Python FastAPI endpoint", "strategy": "balanced"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["cache_hit"])

        # Second identical request hits cache
        r2 = self.client.post(
            "/api/v1/model-router/route",
            json={"prompt": "Write a Python FastAPI endpoint", "strategy": "balanced"},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json()["cache_hit"])

        # Clear cache
        cc = self.client.post("/api/v1/model-router/cache/clear")
        self.assertEqual(cc.status_code, 200)
        self.assertGreaterEqual(cc.json()["cleared_entries"], 1)

        # Benchmark
        b = self.client.post(
            "/api/v1/model-router/benchmark",
            json={"prompt": "Compare REST and WebSockets", "model_ids": ["local-phi4-mini", "gemini-2.5-flash"]},
        )
        self.assertEqual(b.status_code, 200)
        self.assertEqual(len(b.json()["results"]), 2)

        # Logs populated
        logs = self.client.get("/api/v1/model-router/logs")
        self.assertEqual(logs.status_code, 200)
        self.assertGreaterEqual(logs.json()["count"], 2)

    def test_websocket_connection(self) -> None:
        with self.client.websocket_connect("/api/v1/model-router/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
