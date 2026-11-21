"""Integration tests for mounting Module 32 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_32_system_health_diagnostics.backend.app.config import SystemHealthConfig
from modules.module_32_system_health_diagnostics.backend.app.main import mount_module
from modules.module_32_system_health_diagnostics.backend.services.health_engine import SystemHealthEngine


class TestJarvisHostIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="JARVIS Host Core Test")
        cfg = SystemHealthConfig(db_path=str(Path(self._tmp.name) / "host_m32.db"))
        self.engine = SystemHealthEngine(config=cfg)
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_mount_routes_and_state(self) -> None:
        self.assertIs(self.host_app.state.system_health, self.engine)
        st = self.client.get("/api/v1/system-health/status")
        self.assertEqual(st.status_code, 200)
        self.assertFalse(st.json()["simulated"])

        ui = self.client.get("/system-health")
        self.assertEqual(ui.status_code, 200)

    def test_end_to_end_diagnostics_flow(self) -> None:
        res = self.client.post("/api/v1/system-health/diagnostics/run")
        self.assertEqual(res.status_code, 201)
        self.assertIn("health_score", res.json())

        hist = self.client.get("/api/v1/system-health/diagnostics")
        self.assertEqual(hist.status_code, 200)
        self.assertEqual(hist.json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
