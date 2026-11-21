"""REST & WebSocket API tests for JARVIS Module 28 — AI Data Analyst."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from modules.module_28_ai_data_analyst.backend.app.config import DataAnalystConfig
from modules.module_28_ai_data_analyst.backend.app.main import create_app


class TestDataAnalystAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = DataAnalystConfig(db_path=os.path.join(self._tmp.name, "api_m28.db"))
        self.app = create_app(config=cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_ui(self) -> None:
        r_h = self.client.get("/api/v1/ai-data-analyst/health")
        self.assertEqual(r_h.status_code, 200)
        self.assertEqual(r_h.json()["module_id"], "jarvis-module-28-ai-data-analyst")
        self.assertTrue(r_h.json()["simulated"])

        r_m = self.client.get("/api/v1/ai-data-analyst/manifest")
        self.assertEqual(r_m.status_code, 200)
        self.assertEqual(r_m.json()["version"], "1.0.0")

        r_ui = self.client.get("/ai-data-analyst")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("AI Data Analyst", r_ui.text)

    def test_full_rest_workflow(self) -> None:
        csv_text = "dept,spend,tickets\nEng,1200,10\nEng,1300,12\nOps,800,9\nOps,900,85\n"
        r_ds = self.client.post(
            "/api/v1/ai-data-analyst/datasets/csv",
            json={"name": "Dept Spend", "csv_text": csv_text, "description": "Monthly spend"},
        )
        self.assertEqual(r_ds.status_code, 201)
        did = r_ds.json()["dataset_id"]

        r_agg = self.client.post(
            f"/api/v1/ai-data-analyst/datasets/{did}/aggregate",
            json={"group_by": "dept", "metric": "spend", "agg": "sum"},
        )
        self.assertEqual(r_agg.status_code, 200)
        self.assertEqual(r_agg.json()["series"][0]["label"], "Eng")

        r_anom = self.client.post(
            f"/api/v1/ai-data-analyst/datasets/{did}/anomalies",
            json={"column": "tickets", "z_threshold": 1.5},
        )
        self.assertEqual(r_anom.status_code, 200)
        self.assertEqual(r_anom.json()["count"], 1)

        r_ask = self.client.post(
            f"/api/v1/ai-data-analyst/datasets/{did}/ask",
            json={"question": "average spend by dept"},
        )
        self.assertEqual(r_ask.status_code, 200)
        self.assertIn("Eng", r_ask.json()["answer"])

        r_rep = self.client.get(f"/api/v1/ai-data-analyst/datasets/{did}/report.md")
        self.assertEqual(r_rep.status_code, 200)
        self.assertIn("# Data Analysis Report: Dept Spend", r_rep.text)

    def test_websocket_connects(self) -> None:
        with self.client.websocket_connect("/api/v1/ai-data-analyst/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
