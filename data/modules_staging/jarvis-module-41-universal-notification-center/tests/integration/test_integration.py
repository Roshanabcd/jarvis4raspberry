"""Host-app integration tests for Module 41 — Universal Notification Center."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import NotificationConfig
from backend.app.main import mount_module
from backend.services.notification_engine import NotificationEngine


class TestHostIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = NotificationConfig(db_path=str(Path(self._tmp.name) / "host_notifications.db"))
        self.host_app = FastAPI(title="JARVIS Core Host")
        self.engine = mount_module(self.host_app, engine=NotificationEngine(config=cfg), include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_mount_module_exposes_state_and_routes(self) -> None:
        self.assertIs(self.host_app.state.notifications, self.engine)
        res = self.client.get("/api/v1/notifications/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

        hud = self.client.get("/notifications")
        self.assertEqual(hud.status_code, 200)

    def test_status_and_priority_filtering(self) -> None:
        self.client.put(
            "/api/v1/notifications/preferences",
            json={"dnd_enabled": True, "allow_critical_during_dnd": True, "enabled_channels": ["hud"]},
        )
        self.client.post(
            "/api/v1/notifications/items",
            json={"source_module": "m32", "title": "Info", "message": "Muted", "priority": "low", "channels": ["hud"]},
        )
        self.client.post(
            "/api/v1/notifications/items",
            json={"source_module": "m33", "title": "Alert", "message": "Bypassed", "priority": "critical", "channels": ["hud"]},
        )

        suppressed = self.client.get("/api/v1/notifications/items?status=suppressed").json()
        self.assertEqual(suppressed["count"], 1)

        critical = self.client.get("/api/v1/notifications/items?priority=critical").json()
        self.assertEqual(critical["count"], 1)
        self.assertEqual(critical["notifications"][0]["status"], "unread")


if __name__ == "__main__":
    unittest.main()
