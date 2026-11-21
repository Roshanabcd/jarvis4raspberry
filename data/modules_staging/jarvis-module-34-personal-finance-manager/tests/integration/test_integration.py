"""Integration tests for mounting Module 34 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import FinanceConfig
from backend.app.main import mount_module
from backend.services.finance_engine import FinanceEngine


class TestJarvisHostIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="JARVIS Host Core Test")
        cfg = FinanceConfig(db_path=str(Path(self._tmp.name) / "host_m34.db"))
        self.engine = FinanceEngine(config=cfg)
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_mount_routes_and_state(self) -> None:
        self.assertIs(self.host_app.state.finance, self.engine)
        st = self.client.get("/api/v1/finance/status")
        self.assertEqual(st.status_code, 200)
        self.assertFalse(st.json()["simulated"])

        ui = self.client.get("/finance")
        self.assertEqual(ui.status_code, 200)

    def test_end_to_end_goal_and_summary_flow(self) -> None:
        g = self.client.post(
            "/api/v1/finance/goals",
            json={"name": "Workstation GPU", "target_amount": 800.0, "current_amount": 200.0},
        )
        self.assertEqual(g.status_code, 201)
        g_id = g.json()["goal_id"]
        c = self.client.post(f"/api/v1/finance/goals/{g_id}/contribute", json={"amount": 200.0})
        self.assertEqual(c.status_code, 200)
        self.assertEqual(c.json()["progress_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
