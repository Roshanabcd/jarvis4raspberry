"""Pluggable Robot Hardware Adapter contract + Simulated ROS2/GPIO Bridge."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Any, Dict


class RobotHardwareAdapter(ABC):
    adapter_name: str = "abstract_robot_hardware"
    is_simulated: bool = True

    @abstractmethod
    def apply_velocity(
        self,
        state: Dict[str, Any],
        linear_mps: float,
        angular_rps: float,
        duration_s: float,
    ) -> Dict[str, Any]:
        """Apply a bounded velocity command and return updated pose/battery telemetry."""

    @abstractmethod
    def engage_estop(self) -> Dict[str, Any]:
        """Immediately halt all actuators."""


class SimulatedRobotHardwareAdapter(RobotHardwareAdapter):
    adapter_name: str = "simulated_ros2_gpio_bridge"
    is_simulated: bool = True

    def apply_velocity(
        self,
        state: Dict[str, Any],
        linear_mps: float,
        angular_rps: float,
        duration_s: float,
    ) -> Dict[str, Any]:
        heading_rad = math.radians(float(state["heading_deg"]))
        delta_heading_deg = math.degrees(angular_rps * duration_s)
        new_heading_deg = (float(state["heading_deg"]) + delta_heading_deg) % 360.0
        avg_rad = math.radians((float(state["heading_deg"]) + delta_heading_deg / 2.0))
        distance = linear_mps * duration_s
        new_x = round(float(state["x"]) + distance * math.cos(avg_rad), 3)
        new_y = round(float(state["y"]) + distance * math.sin(avg_rad), 3)
        drain = round((abs(linear_mps) * 0.4 + abs(angular_rps) * 0.2) * duration_s, 2)
        new_batt = max(0.0, round(float(state["battery_pct"]) - drain, 2))
        return {
            "x": new_x,
            "y": new_y,
            "heading_deg": round(new_heading_deg, 2),
            "linear_mps": round(linear_mps, 3),
            "angular_rps": round(angular_rps, 3),
            "battery_pct": new_batt,
        }

    def engage_estop(self) -> Dict[str, Any]:
        return {
            "mode": "estop_engaged",
            "estop_engaged": True,
            "linear_mps": 0.0,
            "angular_rps": 0.0,
        }
