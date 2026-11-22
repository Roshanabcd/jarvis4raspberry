"""JARVIS Robot Brain Engine (Module 31).

Provides:
- Safety-first E-STOP interlock with explicit confirmation reset
- Velocity clamping, obstacle proximity halt, and low-battery mission lockout
- Differential-drive 2D pose kinematics
- Named waypoint registry and multi-step autonomous mission execution
"""

from __future__ import annotations

import math
import time
import uuid
from typing import Any, Dict, List, Optional

from backend.adapters.hardware_adapter import RobotHardwareAdapter, SimulatedRobotHardwareAdapter
from backend.app.config import RobotBrainConfig
from backend.models.database import RobotBrainDB, utc_now_iso


class RobotBrainError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class RobotBrainEngine:
    def __init__(
        self,
        config: Optional[RobotBrainConfig] = None,
        db: Optional[RobotBrainDB] = None,
        hardware: Optional[RobotHardwareAdapter] = None,
    ) -> None:
        self.config = config or RobotBrainConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or RobotBrainDB(self.config.db_path)
        self.hardware = hardware or SimulatedRobotHardwareAdapter()
        self._started_at = time.monotonic()

    def _assert_not_estop(self, state: Dict[str, Any]) -> None:
        if state["estop_engaged"]:
            raise RobotBrainError(
                "ESTOP_ENGAGED",
                "Hardware E-STOP is engaged. Clear E-STOP with confirm_reset=true before issuing motion or mission commands.",
                409,
            )

    def engage_estop(self, reason: str) -> Dict[str, Any]:
        patch = self.hardware.engage_estop()
        state = self.db.update_state(**patch)
        self.db.add_event(f"evt_{uuid.uuid4().hex[:10]}", "estop.engaged", reason)
        return state

    def reset_estop(self, confirm_reset: bool, operator_note: str = "") -> Dict[str, Any]:
        if not confirm_reset:
            raise RobotBrainError(
                "ESTOP_RESET_CONFIRMATION_REQUIRED",
                "Clearing E-STOP requires confirm_reset=true after verifying physical clearance.",
                409,
            )
        state = self.db.update_state(estop_engaged=False, mode="idle", linear_mps=0.0, angular_rps=0.0)
        self.db.add_event(f"evt_{uuid.uuid4().hex[:10]}", "estop.reset", operator_note or "Operator confirmed reset")
        return state

    def ingest_sensor_reading(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        for key in ("front_obstacle_m", "battery_pct", "cpu_temp_c"):
            if payload.get(key) is not None:
                updates[key] = float(payload[key])
        state = self.db.update_state(**updates) if updates else self.db.get_state()
        self.db.add_event(f"evt_{uuid.uuid4().hex[:10]}", "sensor.update", f"updates={updates}")
        return state

    def send_motion_command(self, linear_mps: float, angular_rps: float, duration_s: float = 1.0) -> Dict[str, Any]:
        state = self.db.get_state()
        self._assert_not_estop(state)

        if linear_mps > 0 and float(state["front_obstacle_m"]) < self.config.min_obstacle_m:
            raise RobotBrainError(
                "OBSTACLE_PROXIMITY_HALT",
                f"Forward motion blocked: obstacle at {state['front_obstacle_m']}m (< {self.config.min_obstacle_m}m clearance).",
                409,
                {"front_obstacle_m": state["front_obstacle_m"], "min_obstacle_m": self.config.min_obstacle_m},
            )

        clamped_lin = max(-self.config.max_linear_mps, min(self.config.max_linear_mps, float(linear_mps)))
        clamped_ang = max(-self.config.max_angular_rps, min(self.config.max_angular_rps, float(angular_rps)))
        hw_out = self.hardware.apply_velocity(state, clamped_lin, clamped_ang, duration_s)
        hw_out["mode"] = "navigating" if (clamped_lin != 0.0 or clamped_ang != 0.0) else "idle"
        updated = self.db.update_state(**hw_out)
        self.db.add_event(
            f"evt_{uuid.uuid4().hex[:10]}",
            "motion.cmd",
            f"lin={clamped_lin}m/s ang={clamped_ang}rad/s dur={duration_s}s -> ({updated['x']}, {updated['y']})",
        )
        return updated

    def create_waypoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        wp = self.db.create_waypoint(
            {
                "waypoint_id": f"wp_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "zone": payload.get("zone", "Main Floor").strip(),
                "x": round(float(payload["x"]), 3),
                "y": round(float(payload["y"]), 3),
                "created_at": utc_now_iso(),
            }
        )
        self.db.add_event(f"evt_{uuid.uuid4().hex[:10]}", "waypoint.created", f"{wp['name']} ({wp['x']}, {wp['y']})")
        return wp

    def create_mission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        for step in payload["steps"]:
            if step["action"] == "navigate_to_waypoint":
                wp_id = step.get("waypoint_id")
                if not wp_id or not self.db.get_waypoint(wp_id):
                    raise RobotBrainError("WAYPOINT_NOT_FOUND", f"Waypoint '{wp_id}' not found.", 404)
        now = utc_now_iso()
        mission = self.db.create_mission(
            {
                "mission_id": f"mis_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "status": "pending",
                "steps": payload["steps"],
                "result": {},
                "created_at": now,
                "updated_at": now,
            }
        )
        self.db.add_event(f"evt_{uuid.uuid4().hex[:10]}", "mission.created", f"{mission['name']} ({len(mission['steps'])} steps)")
        return mission

    def execute_mission(self, mission_id: str) -> Dict[str, Any]:
        mission = self.db.get_mission(mission_id)
        if not mission:
            raise RobotBrainError("MISSION_NOT_FOUND", f"Mission '{mission_id}' not found.", 404)

        state = self.db.get_state()
        self._assert_not_estop(state)

        if float(state["battery_pct"]) < self.config.min_battery_pct:
            raise RobotBrainError(
                "LOW_BATTERY_LOCKOUT",
                f"Mission blocked: battery at {state['battery_pct']}% (< {self.config.min_battery_pct}%).",
                409,
            )

        if float(state["front_obstacle_m"]) < self.config.min_obstacle_m:
            raise RobotBrainError(
                "OBSTACLE_PROXIMITY_HALT",
                f"Mission blocked: obstacle at {state['front_obstacle_m']}m (< {self.config.min_obstacle_m}m).",
                409,
            )

        step_logs: List[Dict[str, Any]] = []
        total_distance_m = 0.0
        cur_x, cur_y = float(state["x"]), float(state["y"])
        cur_batt = float(state["battery_pct"])
        final_mode = "idle"

        for idx, step in enumerate(mission["steps"], start=1):
            action = step["action"]
            if action == "navigate_to_waypoint":
                wp = self.db.get_waypoint(step["waypoint_id"])
                if not wp:
                    raise RobotBrainError("WAYPOINT_NOT_FOUND", f"Waypoint '{step['waypoint_id']}' not found.", 404)
                dist = round(math.hypot(float(wp["x"]) - cur_x, float(wp["y"]) - cur_y), 3)
                total_distance_m = round(total_distance_m + dist, 3)
                cur_x, cur_y = float(wp["x"]), float(wp["y"])
                cur_batt = max(0.0, round(cur_batt - dist * 0.5, 2))
                step_logs.append({"step": idx, "action": action, "target": wp["name"], "distance_m": dist})
            elif action == "inspect_zone":
                cur_batt = max(0.0, round(cur_batt - 0.5, 2))
                step_logs.append({"step": idx, "action": action, "note": step.get("note", "Zone scan complete")})
            elif action == "return_to_dock":
                dist = round(math.hypot(0.0 - cur_x, 0.0 - cur_y), 3)
                total_distance_m = round(total_distance_m + dist, 3)
                cur_x, cur_y = 0.0, 0.0
                cur_batt = max(0.0, round(cur_batt - dist * 0.5, 2))
                final_mode = "charging"
                step_logs.append({"step": idx, "action": action, "distance_m": dist, "docked": True})

        new_state = self.db.update_state(
            x=cur_x, y=cur_y, linear_mps=0.0, angular_rps=0.0, battery_pct=cur_batt, mode=final_mode
        )
        result = {"total_distance_m": total_distance_m, "steps_executed": step_logs, "final_state": new_state}
        updated_mission = self.db.update_mission(mission_id, "completed", result)
        self.db.add_event(
            f"evt_{uuid.uuid4().hex[:10]}",
            "mission.completed",
            f"{mission['name']} ({total_distance_m}m, batt={cur_batt}%)",
        )
        return updated_mission  # type: ignore[return-value]

    def get_status(self) -> Dict[str, Any]:
        state = self.db.get_state()
        return {
            "adapter": self.hardware.adapter_name,
            "simulated": self.hardware.is_simulated,
            "mode": state["mode"],
            "estop_engaged": state["estop_engaged"],
            "pose": {"x": state["x"], "y": state["y"], "heading_deg": state["heading_deg"]},
            "battery_pct": state["battery_pct"],
            "front_obstacle_m": state["front_obstacle_m"],
            "cpu_temp_c": state["cpu_temp_c"],
            "waypoints_count": len(self.db.list_waypoints()),
            "missions_count": len(self.db.list_missions()),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
