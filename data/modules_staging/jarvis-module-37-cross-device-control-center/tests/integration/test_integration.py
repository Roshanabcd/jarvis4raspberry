"""Integration tests for mounting Module 37 inside a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import DeviceMeshConfig
from backend.app.main import mount_module
from backend.services.device_mesh_engine import DeviceMeshEngine


class TestModule37Integration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = DeviceMeshConfig(db_path=str(Path(self._tmp.name) / "host_devices.db"))
        self.engine = DeviceMeshEngine(config=cfg)
        self.host_app = FastAPI(title="JARVIS OS Host")
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_app_state_and_route_mounting(self) -> None:
        self.assertIs(self.host_app.state.devices, self.engine)
        status = self.client.get("/api/v1/devices/status")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["adapter"], "simulated_mesh_device_bridge")
        self.assertTrue(status.json()["simulated"])

    def test_end_to_end_mesh_command_and_clipboard_listing(self) -> None:
        dev = self.client.post(
            "/api/v1/devices/nodes",
            json={"name": "Pi5-Desk", "device_type": "raspberry_pi", "capabilities": ["clipboard", "notifications"]},
        ).json()
        dev_id = dev["device_id"]

        self.client.post(
            f"/api/v1/devices/nodes/{dev_id}/commands",
            json={"capability": "notifications", "action": "ping", "params": {}},
        )
        self.client.post("/api/v1/devices/clipboard", json={"source_device_id": dev_id, "content": "sync-1"})

        cmds = self.client.get(f"/api/v1/devices/commands?device_id={dev_id}")
        self.assertEqual(cmds.status_code, 200)
        self.assertEqual(cmds.json()["count"], 1)

        clips = self.client.get("/api/v1/devices/clipboard")
        self.assertEqual(clips.status_code, 200)
        self.assertEqual(clips.json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
