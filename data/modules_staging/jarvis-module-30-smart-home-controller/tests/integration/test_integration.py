"""Integration tests for mounting Module 30 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import SmartHomeConfig
from backend.app.main import mount_module
from backend.services.smart_home_engine import SmartHomeEngine


class TestJarvisHostIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="JARVIS Host Core Test")
        cfg = SmartHomeConfig(db_path=str(Path(self._tmp.name) / "host_m30.db"))
        self.engine = SmartHomeEngine(config=cfg)
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_mount_routes_and_state(self) -> None:
        self.assertIs(self.host_app.state.smart_home, self.engine)
        res = self.client.get("/api/v1/smart-home/status")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["adapter"], "simulated_iot_home_bridge")

        ui = self.client.get("/smart-home")
        self.assertEqual(ui.status_code, 200)

    def test_end_to_end_sensor_rule_and_energy_flow(self) -> None:
        s = self.client.post(
            "/api/v1/smart-home/devices",
            json={"name": "Studio Sensor", "room": "Studio", "device_type": "sensor", "rated_watts": 1.0},
        ).json()
        ac = self.client.post(
            "/api/v1/smart-home/devices",
            json={"name": "Studio AC", "room": "Studio", "device_type": "thermostat", "rated_watts": 900.0},
        ).json()
        r = self.client.post(
            "/api/v1/smart-home/rules",
            json={
                "name": "Studio Cool",
                "sensor_device_id": s["device_id"],
                "metric_key": "temp_c",
                "operator": ">",
                "threshold": 26.0,
                "target_device_id": ac["device_id"],
                "target_command": "turn_on",
            },
        )
        self.assertEqual(r.status_code, 201)
        self.client.post(
            f"/api/v1/smart-home/devices/{s['device_id']}/command",
            json={"command": "update_reading", "value": {"temp_c": 28.5}},
        )
        ev = self.client.post("/api/v1/smart-home/rules/evaluate")
        self.assertEqual(ev.status_code, 200)
        self.assertEqual(ev.json()["triggered_count"], 1)

        energy = self.client.get("/api/v1/smart-home/energy").json()
        self.assertEqual(energy["total_active_watts"], 900.0)


if __name__ == "__main__":
    unittest.main()
