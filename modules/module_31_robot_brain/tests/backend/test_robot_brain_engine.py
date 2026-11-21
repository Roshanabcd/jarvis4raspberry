"""Unit tests for RobotBrainEngine (JARVIS Module 31)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from modules.module_31_robot_brain.backend.app.config import RobotBrainConfig
from modules.module_31_robot_brain.backend.services.robot_brain_engine import RobotBrainEngine, RobotBrainError


class TestRobotBrainEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = RobotBrainConfig(db_path=str(Path(self._tmp.name) / "test_m31.db"))
        self.engine = RobotBrainEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_estop_interlock_and_confirmed_reset(self) -> None:
        self.engine.engage_estop("Unit test E-STOP")
        with self.assertRaises(RobotBrainError) as ctx:
            self.engine.send_motion_command(0.5, 0.0, 1.0)
        self.assertEqual(ctx.exception.code, "ESTOP_ENGAGED")
        self.assertEqual(ctx.exception.status_code, 409)

        with self.assertRaises(RobotBrainError) as rctx:
            self.engine.reset_estop(confirm_reset=False)
        self.assertEqual(rctx.exception.code, "ESTOP_RESET_CONFIRMATION_REQUIRED")

        cleared = self.engine.reset_estop(confirm_reset=True, operator_note="Clear")
        self.assertFalse(cleared["estop_engaged"])
        self.assertEqual(cleared["mode"], "idle")

    def test_obstacle_halt_and_velocity_clamping(self) -> None:
        moved = self.engine.send_motion_command(linear_mps=3.0, angular_rps=0.0, duration_s=1.0)
        # Clamped to max_linear_mps (1.2 m/s)
        self.assertEqual(moved["x"], 1.2)
        self.assertEqual(moved["linear_mps"], 1.2)

        self.engine.ingest_sensor_reading({"front_obstacle_m": 0.2})
        with self.assertRaises(RobotBrainError) as ctx:
            self.engine.send_motion_command(linear_mps=0.5, angular_rps=0.0, duration_s=1.0)
        self.assertEqual(ctx.exception.code, "OBSTACLE_PROXIMITY_HALT")

    def test_low_battery_lockout_and_mission_execution(self) -> None:
        wp = self.engine.create_waypoint({"name": "Dock A", "zone": "Lab", "x": 3.0, "y": 4.0})
        m = self.engine.create_mission(
            {
                "name": "Lab Inspection",
                "steps": [
                    {"action": "navigate_to_waypoint", "waypoint_id": wp["waypoint_id"]},
                    {"action": "inspect_zone", "note": "Check lab"},
                    {"action": "return_to_dock"},
                ],
            }
        )
        self.engine.ingest_sensor_reading({"battery_pct": 10.0})
        with self.assertRaises(RobotBrainError) as bctx:
            self.engine.execute_mission(m["mission_id"])
        self.assertEqual(bctx.exception.code, "LOW_BATTERY_LOCKOUT")

        self.engine.ingest_sensor_reading({"battery_pct": 85.0})
        res = self.engine.execute_mission(m["mission_id"])
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["result"]["total_distance_m"], 10.0)
        self.assertEqual(res["result"]["final_state"]["mode"], "charging")


if __name__ == "__main__":
    unittest.main()
