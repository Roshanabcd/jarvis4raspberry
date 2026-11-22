"""Integration tests for mounting Module 31 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_31_robot_brain.backend.app.config import RobotBrainConfig
from modules.module_31_robot_brain.backend.app.main import mount_module
from modules.module_31_robot_brain.backend.services.robot_brain_engine import RobotBrainEngine


class TestJarvisHostIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="JARVIS Host Core Test")
        cfg = RobotBrainConfig(db_path=str(Path(self._tmp.name) / "host_m31.db"))
        self.engine = RobotBrainEngine(config=cfg)
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_mount_routes_and_state(self) -> None:
        self.assertIs(self.host_app.state.robot_brain, self.engine)
        st = self.client.get("/api/v1/robot-brain/status")
        self.assertEqual(st.status_code, 200)
        self.assertEqual(st.json()["adapter"], "simulated_ros2_gpio_bridge")

        ui = self.client.get("/robot-brain")
        self.assertEqual(ui.status_code, 200)

    def test_end_to_end_waypoint_and_mission_flow(self) -> None:
        wp = self.client.post(
            "/api/v1/robot-brain/waypoints",
            json={"name": "Server Rack", "zone": "Data Room", "x": 6.0, "y": 8.0},
        )
        self.assertEqual(wp.status_code, 201)
        wp_id = wp.json()["waypoint_id"]

        m = self.client.post(
            "/api/v1/robot-brain/missions",
            json={
                "name": "Server Rack Patrol",
                "steps": [
                    {"action": "navigate_to_waypoint", "waypoint_id": wp_id},
                    {"action": "return_to_dock"},
                ],
            },
        )
        self.assertEqual(m.status_code, 201)
        ex = self.client.post(f"/api/v1/robot-brain/missions/{m.json()['mission_id']}/execute")
        self.assertEqual(ex.status_code, 200)
        self.assertEqual(ex.json()["status"], "completed")
        self.assertEqual(ex.json()["result"]["total_distance_m"], 20.0)


if __name__ == "__main__":
    unittest.main()
