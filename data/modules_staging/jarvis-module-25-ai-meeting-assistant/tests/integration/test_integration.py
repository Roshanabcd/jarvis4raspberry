"""Integration tests for mounting Module 25 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import MeetingAssistantConfig
from backend.app.main import mount_module
from backend.services.meeting_engine import MeetingAssistantEngine


class TestHostMountIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="Simulated JARVIS OS Host")

        @self.host_app.get("/")
        async def host_root():
            return {"host": "jarvis-os-core"}

        cfg = MeetingAssistantConfig(db_path=os.path.join(self._tmp.name, "host_m25.db"))
        engine = MeetingAssistantEngine(config=cfg)
        mount_module(self.host_app, engine=engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_root_preserved_and_module_mounted(self) -> None:
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertEqual(r_root.json()["host"], "jarvis-os-core")

        r_ui = self.client.get("/meeting-assistant")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("Module 25", r_ui.text)

        r_health = self.client.get("/api/v1/meeting-assistant/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["status"], "ok")

    def test_persistence_across_engine_restarts(self) -> None:
        db_path = os.path.join(self._tmp.name, "persist_m25.db")
        eng1 = MeetingAssistantEngine(config=MeetingAssistantConfig(db_path=db_path))
        created = eng1.create_meeting({"title": "Persistence Check", "meeting_date": "2026-11-20"})
        eng1.add_segment(created["meeting_id"], "Roshan", "We confirmed WAL durability.", 5)

        eng2 = MeetingAssistantEngine(config=MeetingAssistantConfig(db_path=db_path))
        loaded = eng2.db.get_meeting(created["meeting_id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["title"], "Persistence Check")
        self.assertEqual(len(eng2.db.list_segments(created["meeting_id"])), 1)


if __name__ == "__main__":
    unittest.main()
