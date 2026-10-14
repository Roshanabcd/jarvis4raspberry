"""Robotics domain agent for JARVIS OS."""

import json
import logging
import re
from typing import Any, Dict, Optional
from ai.agents.base_agent import BaseAgent
from config.config_manager import config

logger = logging.getLogger("JARVIS-ROBOTICS-AGENT")


class RoboticsAgent(BaseAgent):
    """Specialized agent for robot locomotion, actuators, and servo manipulation."""

    def __init__(self):
        super().__init__(
            name="RoboticsAgent",
            description="Executes motion control, servo positioning, and hardware safety commands for the robot platform.",
        )
        self.simulation_mode = config.get("simulation_mode", True)
        self._init_controller()

    def _init_controller(self):
        """Safely import and initialize the robot controller."""
        try:
            from tools.robotics.controller import robot
            self.robot = robot
        except Exception as exc:
            logger.warning("Could not initialize RobotController; using fallback simulation: %s", exc)
            self.robot = None

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Parse robot command query and execute movement or servo adjustments.

        Args:
            query: Instruction query string (e.g. 'move forward speed 50', 'stop', 'servo 0 to 90').
            context: Optional execution context.

        Returns:
            Structured JSON string detailing the action taken and system state.
        """
        q = query.lower().strip()
        logger.info("RoboticsAgent processing query: '%s'", query)

        result: Dict[str, Any] = {
            "agent": self.name,
            "query": query,
            "simulation_mode": self.simulation_mode,
            "success": True,
            "action": "unknown",
            "details": {},
        }

        try:
            if "estop" in q or "emergency stop" in q:
                if self.robot and hasattr(self.robot, "emergency_stop"):
                    self.robot.emergency_stop()
                result["action"] = "emergency_stop"
                result["details"] = {"status": "EMERGENCY_STOP", "message": "Emergency stop initiated immediately."}

            elif "stop" in q or "halt" in q:
                if self.robot and hasattr(self.robot, "stop"):
                    self.robot.stop()
                result["action"] = "stop"
                result["details"] = {"status": "STOPPED", "message": "Motors halted."}

            elif "forward" in q:
                # Extract speed if present (e.g. 'forward speed 60' or 'forward 80')
                speed_match = re.search(r"(?:speed\s*|forward\s*)(\d+)", q)
                speed = int(speed_match.group(1)) if speed_match else 50
                speed = max(0, min(100, speed))

                if self.robot and hasattr(self.robot, "forward"):
                    self.robot.forward(speed)
                result["action"] = "forward"
                result["details"] = {"speed": speed, "message": f"Moving forward at speed {speed}."}

            elif "servo" in q:
                # Parse channel and angle: e.g. "set servo 1 to 90" or "servo channel 0 angle 45"
                chan_match = re.search(r"(?:channel\s*|servo\s*)(\d+)", q)
                angle_match = re.search(r"(?:angle\s*|to\s*)(\d+)", q)

                channel = int(chan_match.group(1)) if chan_match else 0
                angle = int(angle_match.group(1)) if angle_match else 90
                angle = max(0, min(180, angle))

                if self.robot and hasattr(self.robot, "set_servo"):
                    self.robot.set_servo(channel, angle)
                result["action"] = "set_servo"
                result["details"] = {"channel": channel, "angle": angle, "message": f"Servo {channel} set to {angle}°."}

            elif "state" in q or "status" in q:
                current_state = getattr(self.robot, "state", "IDLE") if self.robot else "SIMULATED_IDLE"
                result["action"] = "status"
                result["details"] = {"state": current_state, "message": f"Robot state is {current_state}."}

            else:
                result["success"] = False
                result["action"] = "unrecognized_command"
                result["details"] = {
                    "message": "Command not recognized by RoboticsAgent. Supported: forward, stop, estop, servo, status.",
                }

        except Exception as exc:
            logger.error("RoboticsAgent execution error: %s", exc, exc_info=True)
            result["success"] = False
            result["action"] = "error"
            result["details"] = {"error": str(exc), "message": "An error occurred while executing the robot command."}

        return json.dumps(result, indent=2)
