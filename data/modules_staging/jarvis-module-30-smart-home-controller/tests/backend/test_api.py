"""FastAPI REST & WebSocket tests for JARVIS Module 30 — Smart Home Controller."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import SmartHomeConfig
from backend.app.main import create_app


class TestSmartHomeAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = SmartHomeConfig(db_path=str(Path(self._tmp.name) / "api_m30.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_ui_route(self) -> None:
        h = self.client.get("/api/v1/smart-home/health")
        self.assertEqual(h.status_code, 200)
        body = h.json()
        self.assertEqual(body["module_id"], "jarvis-module-30-smart-home-controller")
        self.assertTrue(body["simulated"])

        m = self.client.get("/api/v1/smart-home/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8130)

        ui = self.client.get("/smart-home")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("SMART HOME CONTROLLER", ui.text)

    def test_device_lock_safety_and_scene_endpoints(self) -> None:
        r1 = self.client.post(
            "/api/v1/smart-home/devices",
            json={"name": "Gate Lock", "room": "Porch", "device_type": "lock", "rated_watts": 3.0},
        )
        self.assertEqual(r1.status_code, 201)
        lock_id = r1.json()["device_id"]

        blocked = self.client.post(
            f"/api/v1/smart-home/devices/{lock_id}/command",
            json={"command": "unlock", "confirm_unlock": False},
        )
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["error"]["code"], "UNLOCK_CONFIRMATION_REQUIRED")

        ok = self.client.post(
            f"/api/v1/smart-home/devices/{lock_id}/command",
            json={"command": "unlock", "confirm_unlock": True},
        )
        self.assertEqual(ok.status_code, 200)
        self.assertFalse(ok.json()["state"]["locked"])

        sc = self.client.post(
            "/api/v1/smart-home/scenes",
            json={
                "name": "Night Lock",
                "description": "Secure porch gate",
                "actions": [{"device_id": lock_id, "command": "lock"}],
            },
        )
        self.assertEqual(sc.status_code, 201)
        act = self.client.post(f"/api/v1/smart-home/scenes/{sc.json()['scene_id']}/activate")
        self.assertEqual(act.status_code, 200)
        self.assertEqual(act.json()["applied_count"], 1)

    def test_websocket_events_stream(self) -> None:
        with self.client.websocket_connect("/api/v1/smart-home/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
