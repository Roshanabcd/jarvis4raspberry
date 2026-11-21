"""Unit tests for SystemHealthEngine (JARVIS Module 32)."""

from __future__ import annotations

import socket
import tempfile
import unittest
from pathlib import Path

from modules.module_32_system_health_diagnostics.backend.app.config import SystemHealthConfig
from modules.module_32_system_health_diagnostics.backend.services.health_engine import SystemHealthEngine, SystemHealthError


class TestSystemHealthEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = SystemHealthConfig(db_path=str(Path(self._tmp.name) / "test_m32.db"))
        self.engine = SystemHealthEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_real_host_metrics_and_alert_ack(self) -> None:
        self.assertFalse(self.engine.probe.is_simulated)
        m = self.engine.get_live_metrics()
        self.assertGreater(m["disk_total_gb"], 0.0)
        self.assertGreaterEqual(m["cpu_count"], 1)

        self.engine.create_rule(
            {"name": "Disk Check", "metric_key": "disk_used_pct", "operator": ">=", "threshold": 0.0, "severity": "warning"}
        )
        cap = self.engine.capture_snapshot()
        self.assertEqual(len(cap["triggered_alerts"]), 1)
        alert_id = cap["triggered_alerts"][0]["alert_id"]
        acked = self.engine.ack_alert(alert_id)
        self.assertTrue(acked["acknowledged"])

    def test_service_probe_ssrf_guard_and_live_tcp_probe(self) -> None:
        with self.assertRaises(SystemHealthError) as ctx:
            self.engine.register_service({"name": "External Host", "host": "8.8.8.8", "port": 53})
        self.assertEqual(ctx.exception.code, "HOST_NOT_ALLOWED")
        self.assertEqual(ctx.exception.status_code, 403)

        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        try:
            self.engine.register_service({"name": "Local Test Socket", "host": "127.0.0.1", "port": port})
            res = self.engine.probe_all_services()
            self.assertEqual(res["count"], 1)
            self.assertEqual(res["services"][0]["last_status"], "up")
            self.assertIsNotNone(res["services"][0]["last_latency_ms"])
        finally:
            srv.close()

    def test_diagnostic_scoring(self) -> None:
        diag = self.engine.run_diagnostics()
        self.assertGreaterEqual(diag["health_score"], 0)
        self.assertLessEqual(diag["health_score"], 100)
        self.assertTrue(len(diag["summary"]["recommendations"]) >= 1)


if __name__ == "__main__":
    unittest.main()
