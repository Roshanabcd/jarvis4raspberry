"""Integration tests for mounting Module 26 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_26_project_autopilot.backend.app.config import ProjectAutopilotConfig
from modules.module_26_project_autopilot.backend.app.main import mount_module
from modules.module_26_project_autopilot.backend.services.autopilot_engine import ProjectAutopilotEngine


class TestHostMountIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="Simulated JARVIS OS Host")

        @self.host_app.get("/")
        async def host_root():
            return {"host": "jarvis-os-core"}

        cfg = ProjectAutopilotConfig(
            db_path=os.path.join(self._tmp.name, "host_m26.db"),
            workspace_root=os.path.join(self._tmp.name, "workspaces"),
        )
        engine = ProjectAutopilotEngine(config=cfg)
        mount_module(self.host_app, engine=engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_root_preserved_and_module_mounted(self) -> None:
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertEqual(r_root.json()["host"], "jarvis-os-core")

        r_ui = self.client.get("/project-autopilot")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("Module 26", r_ui.text)

        r_health = self.client.get("/api/v1/project-autopilot/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["status"], "ok")

    def test_persistence_across_engine_restarts(self) -> None:
        db_path = os.path.join(self._tmp.name, "persist_m26.db")
        ws_root = os.path.join(self._tmp.name, "persist_ws")
        eng1 = ProjectAutopilotEngine(config=ProjectAutopilotConfig(db_path=db_path, workspace_root=ws_root))
        created = eng1.create_project({"name": "Durability Check", "goal": "Verify SQLite WAL persistence."})
        pid = created["project"]["project_id"]
        eng1.advance_project(pid, max_steps=2)

        eng2 = ProjectAutopilotEngine(config=ProjectAutopilotConfig(db_path=db_path, workspace_root=ws_root))
        loaded = eng2.get_project_bundle(pid)
        self.assertEqual(loaded["project"]["name"], "Durability Check")
        self.assertEqual(loaded["progress_pct"], 40.0)


if __name__ == "__main__":
    unittest.main()
