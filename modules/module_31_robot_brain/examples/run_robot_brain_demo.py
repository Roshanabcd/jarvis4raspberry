"""Runnable CLI demo for JARVIS Module 31 — JARVIS Robot Brain."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_31_robot_brain.backend.app.config import RobotBrainConfig
from modules.module_31_robot_brain.backend.services.robot_brain_engine import RobotBrainEngine, RobotBrainError


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = RobotBrainConfig(db_path=str(Path(tmp) / "demo_robot_brain.db"))
        engine = RobotBrainEngine(config=cfg)

        # 1. Motion command with kinematics
        moved = engine.send_motion_command(linear_mps=1.0, angular_rps=0.0, duration_s=2.0)

        # 2. Engage E-STOP & verify motion is blocked
        engine.engage_estop("Demo safety test")
        estop_blocked_code = None
        try:
            engine.send_motion_command(0.5, 0.0, 1.0)
        except RobotBrainError as exc:
            estop_blocked_code = exc.code

        # 3. Confirmed E-STOP reset
        engine.reset_estop(confirm_reset=True, operator_note="Path clear")

        # 4. Waypoints & autonomous patrol mission
        wp = engine.create_waypoint({"name": "Lab Bench", "zone": "Workshop", "x": 5.0, "y": 4.0})
        mission = engine.create_mission(
            {
                "name": "Workshop Patrol",
                "steps": [
                    {"action": "navigate_to_waypoint", "waypoint_id": wp["waypoint_id"]},
                    {"action": "inspect_zone", "note": "Thermal & perimeter check"},
                    {"action": "return_to_dock"},
                ],
            }
        )
        completed = engine.execute_mission(mission["mission_id"])

        print(
            json.dumps(
                {
                    "simulated": engine.hardware.is_simulated,
                    "after_motion_pose": {"x": moved["x"], "y": moved["y"]},
                    "estop_blocked_code": estop_blocked_code,
                    "mission_status": completed["status"],
                    "mission_distance_m": completed["result"]["total_distance_m"],
                    "final_status": engine.get_status(),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
