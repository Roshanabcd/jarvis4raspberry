"""Integration tests for mounting Module 33 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_33_defensive_cybersecurity_agent.backend.app.config import CyberSecurityConfig
from modules.module_33_defensive_cybersecurity_agent.backend.app.main import mount_module
from modules.module_33_defensive_cybersecurity_agent.backend.services.security_engine import DefensiveSecurityEngine


class TestJarvisHostIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.scan_root = Path(self._tmp.name) / "scan_root"
        self.scan_root.mkdir()
        (self.scan_root / "config.ini").write_text("mode=prod\n", encoding="utf-8")
        self.host_app = FastAPI(title="JARVIS Host Core Test")
        cfg = CyberSecurityConfig(
            db_path=str(Path(self._tmp.name) / "host_m33.db"),
            scan_root=str(self.scan_root),
        )
        self.engine = DefensiveSecurityEngine(config=cfg)
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_mount_routes_and_state(self) -> None:
        self.assertIs(self.host_app.state.cybersecurity, self.engine)
        st = self.client.get("/api/v1/cybersecurity/status")
        self.assertEqual(st.status_code, 200)
        self.assertFalse(st.json()["simulated"])
        self.assertEqual(st.json()["posture_score"], 100)

        ui = self.client.get("/cybersecurity")
        self.assertEqual(ui.status_code, 200)

    def test_end_to_end_fim_drift_workflow(self) -> None:
        bl = self.client.post(
            "/api/v1/cybersecurity/fim/baseline",
            json={"name": "Host Config", "relative_path": "."},
        )
        self.assertEqual(bl.status_code, 201)
        bl_id = bl.json()["baseline_id"]

        (self.scan_root / "config.ini").write_text("mode=debug\n", encoding="utf-8")
        ver = self.client.post(f"/api/v1/cybersecurity/fim/verify/{bl_id}")
        self.assertEqual(ver.status_code, 200)
        self.assertTrue(ver.json()["drift_detected"])

        st = self.client.get("/api/v1/cybersecurity/status").json()
        self.assertLess(st["posture_score"], 100)


if __name__ == "__main__":
    unittest.main()
