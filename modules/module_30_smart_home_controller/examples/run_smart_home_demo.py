"""Runnable CLI demo for JARVIS Module 30 — Smart Home Controller."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_30_smart_home_controller.backend.app.config import SmartHomeConfig
from modules.module_30_smart_home_controller.backend.services.smart_home_engine import SmartHomeEngine, SmartHomeError


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = SmartHomeConfig(db_path=str(Path(tmp) / "demo_smart_home.db"))
        engine = SmartHomeEngine(config=cfg)

        lamp = engine.register_device(
            {"name": "Living Room Lamp", "room": "Living Room", "device_type": "light", "rated_watts": 20.0}
        )
        ac = engine.register_device(
            {"name": "Bedroom AC", "room": "Bedroom", "device_type": "thermostat", "rated_watts": 1200.0}
        )
        lock = engine.register_device(
            {"name": "Front Door Lock", "room": "Entryway", "device_type": "lock", "rated_watts": 2.0}
        )
        sensor = engine.register_device(
            {"name": "Bedroom Temp Sensor", "room": "Bedroom", "device_type": "sensor", "rated_watts": 1.0}
        )

        # 1. Verify safety gate blocks unconfirmed unlock
        blocked_code = None
        try:
            engine.send_command(lock["device_id"], "unlock", confirm_unlock=False)
        except SmartHomeError as exc:
            blocked_code = exc.code

        # 2. Confirmed unlock succeeds
        unlocked = engine.send_command(lock["device_id"], "unlock", confirm_unlock=True)

        # 3. Create & activate Evening Scene
        scene = engine.create_scene(
            {
                "name": "Evening Mode",
                "description": "Dim living room lamp to 50% and lock front door",
                "actions": [
                    {"device_id": lamp["device_id"], "command": "turn_on"},
                    {"device_id": lamp["device_id"], "command": "set_brightness", "value": 50},
                    {"device_id": lock["device_id"], "command": "lock"},
                ],
            }
        )
        scene_res = engine.activate_scene(scene["scene_id"])

        # 4. Create sensor rule & trigger it
        engine.create_rule(
            {
                "name": "Cool Bedroom Above 28C",
                "sensor_device_id": sensor["device_id"],
                "metric_key": "temp_c",
                "operator": ">",
                "threshold": 28.0,
                "target_device_id": ac["device_id"],
                "target_command": "turn_on",
            }
        )
        engine.send_command(sensor["device_id"], "update_reading", value={"temp_c": 30.2})
        rule_res = engine.evaluate_rules()

        summary = {
            "simulated": engine.bridge.is_simulated,
            "unconfirmed_unlock_blocked_code": blocked_code,
            "confirmed_unlock_locked_state": unlocked["state"]["locked"],
            "scene_applied_count": scene_res["applied_count"],
            "rules_triggered_count": rule_res["triggered_count"],
            "energy": engine.get_energy_summary(),
            "status": engine.get_status(),
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
