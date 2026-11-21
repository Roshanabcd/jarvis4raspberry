"""FastAPI REST & WebSocket tests for JARVIS Module 32 — System Health & Diagnostics."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.module_32_system_health_diagnostics.backend.app.config import SystemHealthConfig
from modules.module_32_system_health_diagnostics.backend.app.main import create_app


class TestSystemHealthAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = SystemHealthConfig(db_path=str(Path(self._tmp.name) / "api_m32.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_ui_route(self) -> None:
        h = self.client.get("/api/v1/system-health/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-32-system-health-diagnostics")
        self.assertFalse(h.json()["simulated"])

        m = self.client.get("/api/v1/system-health/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8132)

        ui = self.client.get("/system-health")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("SYSTEM HEALTH", ui.text)

    def test_metrics_rules_alerts_and_ssrf_guard(self) -> None:
        live = self.client.get("/api/v1/system-health/metrics")
        self.assertEqual(live.status_code, 200)
        self.assertIn("disk_used_pct", live.json()["metrics"])

        bad = self.client.post(
            "/api/v1/system-health/services",
            json={"name": "Bad Remote", "host": "1.1.1.1", "port": 80},
        )
        self.assertEqual(bad.status_code, 403)
        self.assertEqual(bad.json()["error"]["code"], "HOST_NOT_ALLOWED")

        r = self.client.post(
            "/api/v1/system-health/rules",
            json={"name": "Low Threshold", "metric_key": "disk_used_pct", "operator": ">=", "threshold": 0.0, "severity": "warning"},
        )
        self.assertEqual(r.status_code, 201)
        cap = self.client.post("/api/v1/system-health/snapshots/capture")
        self.assertEqual(cap.status_code, 201)
        alert_id = cap.json()["triggered_alerts"][0]["alert_id"]
        ack = self.client.post(f"/api/v1/system-health/alerts/{alert_id}/ack")
        self.assertEqual(ack.status_code, 200)
        self.assertTrue(ack.json()["acknowledged"])

    def test_websocket_metrics_stream(self) -> None:
        with self.client.websocket_connect("/api/v1/system-health/ws/metrics") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
