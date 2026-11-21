"""REST & WebSocket API tests for Module 41 — Universal Notification Center."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.module_41_universal_notification_center.backend.app.config import NotificationConfig
from modules.module_41_universal_notification_center.backend.app.main import create_app


class TestNotificationsAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = NotificationConfig(db_path=str(Path(self._tmp.name) / "api_notifications.db"))
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_status_and_hud(self) -> None:
        h = self.client.get("/api/v1/notifications/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-41-universal-notification-center")
        self.assertFalse(h.json()["simulated"])

        m = self.client.get("/api/v1/notifications/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8141)

        s = self.client.get("/api/v1/notifications/status")
        self.assertEqual(s.status_code, 200)
        self.assertEqual(s.json()["adapter"], "local_notification_hub_engine")

        hud = self.client.get("/notifications")
        self.assertEqual(hud.status_code, 200)
        self.assertIn("Universal Notification Center", hud.text)

    def test_preferences_send_ack_dismiss_and_errors(self) -> None:
        pref_res = self.client.put(
            "/api/v1/notifications/preferences",
            json={"dnd_enabled": True, "allow_critical_during_dnd": True, "enabled_channels": ["hud", "desktop"]},
        )
        self.assertEqual(pref_res.status_code, 200)
        self.assertTrue(pref_res.json()["dnd_enabled"])

        created = self.client.post(
            "/api/v1/notifications/items",
            json={
                "source_module": "module-40-approvals",
                "title": "High-Risk Approval Required",
                "message": "Shell action awaiting confirmation.",
                "priority": "critical",
                "channels": ["hud", "desktop"],
                "dedupe_key": "approval-req-01",
            },
        )
        self.assertEqual(created.status_code, 201)
        nid = created.json()["notification_id"]
        self.assertEqual(created.json()["status"], "unread")

        ack = self.client.post(f"/api/v1/notifications/items/{nid}/ack")
        self.assertEqual(ack.status_code, 200)
        self.assertEqual(ack.json()["status"], "acknowledged")

        dismiss = self.client.post(f"/api/v1/notifications/items/{nid}/dismiss")
        self.assertEqual(dismiss.status_code, 200)
        self.assertEqual(dismiss.json()["status"], "dismissed")

        bad = self.client.post(
            "/api/v1/notifications/items",
            json={
                "source_module": "module-41",
                "title": "Invalid",
                "message": "Bad priority",
                "priority": "extreme",
                "channels": ["hud"],
            },
        )
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["error"]["code"], "INVALID_PRIORITY")

    def test_websocket_stream(self) -> None:
        with self.client.websocket_connect("/api/v1/notifications/ws/stream") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertEqual(msg["status"]["adapter"], "local_notification_hub_engine")


if __name__ == "__main__":
    unittest.main()
