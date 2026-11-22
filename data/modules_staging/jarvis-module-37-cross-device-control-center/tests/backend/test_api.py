"""FastAPI REST & WebSocket API tests for JARVIS Module 37 — Cross-Device Control Center."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import DeviceMeshConfig
from backend.app.main import create_app


class TestDeviceMeshAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = DeviceMeshConfig(db_path=str(Path(self._tmp.name) / "api_devices.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_hud(self) -> None:
        r = self.client.get("/api/v1/devices/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["module_id"], "jarvis-module-37-cross-device-control-center")
        self.assertTrue(body["simulated"])

        m = self.client.get("/api/v1/devices/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8137)

        hud = self.client.get("/devices")
        self.assertEqual(hud.status_code, 200)
        self.assertIn("Cross-Device Control Center", hud.text)

    def test_register_command_clipboard_and_offline_error(self) -> None:
        created = self.client.post(
            "/api/v1/devices/nodes",
            json={
                "name": "MacBook-Pro",
                "device_type": "laptop",
                "platform": "macos",
                "capabilities": ["clipboard", "media", "notifications"],
                "battery_pct": 92,
                "online": True,
            },
        )
        self.assertEqual(created.status_code, 201)
        dev_id = created.json()["device_id"]

        cmd = self.client.post(
            f"/api/v1/devices/nodes/{dev_id}/commands",
            json={"capability": "media", "action": "pause", "params": {}},
        )
        self.assertEqual(cmd.status_code, 201)
        self.assertTrue(cmd.json()["simulated"])

        clip = self.client.post(
            "/api/v1/devices/clipboard",
            json={"source_device_id": dev_id, "content": "Shared note across mesh"},
        )
        self.assertEqual(clip.status_code, 201)
        self.assertEqual(len(clip.json()["sha256"]), 64)

        self.client.post(f"/api/v1/devices/nodes/{dev_id}/heartbeat", json={"online": False, "battery_pct": 88})
        blocked = self.client.post(
            f"/api/v1/devices/nodes/{dev_id}/commands",
            json={"capability": "media", "action": "play", "params": {}},
        )
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["error"]["code"], "DEVICE_OFFLINE")

    def test_websocket_mesh_channel(self) -> None:
        with self.client.websocket_connect("/api/v1/devices/ws/mesh") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertEqual(msg["status"]["adapter"], "simulated_mesh_device_bridge")
            self.assertTrue(msg["status"]["simulated"])


if __name__ == "__main__":
    unittest.main()
