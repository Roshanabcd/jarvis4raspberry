"""Integration tests for mounting Module 28 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_28_ai_data_analyst.backend.app.config import DataAnalystConfig
from modules.module_28_ai_data_analyst.backend.app.main import mount_module
from modules.module_28_ai_data_analyst.backend.services.analyst_engine import DataAnalystEngine


class TestHostMountIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="Simulated JARVIS OS Host")

        @self.host_app.get("/")
        async def host_root():
            return {"host": "jarvis-os-core"}

        cfg = DataAnalystConfig(db_path=os.path.join(self._tmp.name, "host_m28.db"))
        engine = DataAnalystEngine(config=cfg)
        mount_module(self.host_app, engine=engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_root_preserved_and_module_mounted(self) -> None:
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertEqual(r_root.json()["host"], "jarvis-os-core")

        r_ui = self.client.get("/ai-data-analyst")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("Module 28", r_ui.text)

        r_health = self.client.get("/api/v1/ai-data-analyst/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["status"], "ok")

    def test_persistence_across_engine_restarts(self) -> None:
        db_path = os.path.join(self._tmp.name, "persist_m28.db")
        eng1 = DataAnalystEngine(config=DataAnalystConfig(db_path=db_path))
        ds = eng1.ingest_rows("Persist Set", [{"k": "a", "v": 10}, {"k": "b", "v": 20}])

        eng2 = DataAnalystEngine(config=DataAnalystConfig(db_path=db_path))
        loaded = eng2.db.get_dataset(ds["dataset_id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["row_count"], 2)


if __name__ == "__main__":
    unittest.main()
