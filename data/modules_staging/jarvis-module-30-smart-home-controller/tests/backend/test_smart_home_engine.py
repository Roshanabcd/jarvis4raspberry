"""Unit tests for SmartHomeEngine (JARVIS Module 30)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.config import SmartHomeConfig
from backend.services.smart_home_engine import SmartHomeEngine, SmartHomeError


class TestSmartHomeEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = SmartHomeConfig(db_path=str(Path(self._tmp.name) / "test_m30.db"))
        self.engine = SmartHomeEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_register_and_light_energy_scaling(self) -> None:
        lamp = self.engine.register_device(
            {"name": "Desk Lamp", "room": "Office", "device_type": "light", "rated_watts": 20.0}
        )
        self.assertEqual(lamp["state"]["power"], "off")
        self.engine.send_command(lamp["device_id"], "turn_on")
        self.engine.send_command(lamp["device_id"], "set_brightness", value=50)
        energy = self.engine.get_energy_summary()
        self.assertEqual(energy["total_active_watts"], 10.0)
        self.assertEqual(energy["by_room"]["Office"], 10.0)

    def test_lock_requires_explicit_confirmation(self) -> None:
        lock = self.engine.register_device(
            {"name": "Main Door", "room": "Entryway", "device_type": "lock", "rated_watts": 2.0}
        )
        with self.assertRaises(SmartHomeError) as ctx:
            self.engine.send_command(lock["device_id"], "unlock", confirm_unlock=False)
        self.assertEqual(ctx.exception.code, "UNLOCK_CONFIRMATION_REQUIRED")
        self.assertEqual(ctx.exception.status_code, 409)

        unlocked = self.engine.send_command(lock["device_id"], "unlock", confirm_unlock=True)
        self.assertFalse(unlocked["state"]["locked"])

    def test_scene_activation_and_rule_evaluation(self) -> None:
        sensor = self.engine.register_device(
            {"name": "Hall Sensor", "room": "Hall", "device_type": "sensor", "rated_watts": 1.0}
        )
        fan = self.engine.register_device(
            {"name": "Hall Fan", "room": "Hall", "device_type": "smart_plug", "rated_watts": 60.0}
        )
        scene = self.engine.create_scene(
            {
                "name": "All Off",
                "description": "Power down fan",
                "actions": [{"device_id": fan["device_id"], "command": "turn_off"}],
            }
        )
        self.engine.create_rule(
            {
                "name": "Hot Hall Auto Fan",
                "sensor_device_id": sensor["device_id"],
                "metric_key": "temp_c",
                "operator": ">=",
                "threshold": 27.5,
                "target_device_id": fan["device_id"],
                "target_command": "turn_on",
            }
        )
        self.engine.send_command(sensor["device_id"], "update_reading", value={"temp_c": 29.0})
        eval_res = self.engine.evaluate_rules()
        self.assertEqual(eval_res["triggered_count"], 1)
        self.assertEqual(self.engine.get_energy_summary()["total_active_watts"], 60.0)

        act_res = self.engine.activate_scene(scene["scene_id"])
        self.assertEqual(act_res["applied_count"], 1)
        self.assertEqual(self.engine.get_energy_summary()["total_active_watts"], 0.0)


if __name__ == "__main__":
    unittest.main()
