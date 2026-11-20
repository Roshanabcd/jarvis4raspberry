"""
JARVIS OS Robot Controller
Unified, safe robotics hardware interface.
Enforces:
- Disarmed startup state (motors disabled until explicitly armed).
- Hard emergency-stop locking (no motion until e-stop is explicitly cleared).
- Speed clamping to configured safe limits.
- Servo channel and angle bounds validation.
"""
import logging
import threading
from typing import Optional, Dict, Any
from config.config_manager import config
from hardware.pca9685.driver import PCA9685
from hardware.esp32.serial_comm import ESP32Controller

logger = logging.getLogger("JARVIS-ROBOTICS")


class RobotController:
    """
    Unified robot motion and actuator controller.
    Enforces actuator safety:
    1. Actuators boot in a DISARMED state.
    2. Emergency stop immediately cuts motors and locks out further motion commands.
    3. Emergency stop must be explicitly cleared via clear_emergency_stop().
    4. Channel & angle boundaries strictly enforced.
    """

    def __init__(self, servo_controller: Optional[PCA9685] = None,
                 motor_controller: Optional[ESP32Controller] = None):
        self.simulated = bool(config.get("simulation_mode", True))
        self.state = "IDLE"
        self.armed = False  # Mandatory safety: boot in DISARMED state
        self._emergency_stopped = False

        robot_cfg = config.get("robot", {}) if hasattr(config, "get") else {}
        self.default_speed = int(robot_cfg.get("default_speed", 50))
        self.max_speed = int(robot_cfg.get("max_speed", 100))

        self.servo_controller = servo_controller or PCA9685()
        self.motor_controller = motor_controller or ESP32Controller()

        logger.info(
            "RobotController initialized (simulated=%s, default_speed=%d, armed=%s)",
            self.simulated, self.default_speed, self.armed
        )

    def arm(self) -> Dict[str, Any]:
        """Arm actuators to permit movement."""
        if self._emergency_stopped:
            logger.warning("Cannot arm robot: EMERGENCY STOP is active. Clear e-stop first.")
            return {"status": "error", "error": "Emergency stop is active", "armed": False}
        self.armed = True
        logger.info("Actuators ARMED.")
        return {"status": "ok", "armed": True}

    def disarm(self) -> Dict[str, Any]:
        """Disarm actuators to prevent unintended movement."""
        self.stop()
        self.armed = False
        logger.info("Actuators DISARMED.")
        return {"status": "ok", "armed": False}

    def _validate_motion(self, speed: Optional[int] = None) -> tuple[bool, int, Optional[str]]:
        """Validate if motion is safe and return clamped speed."""
        if self._emergency_stopped or self.state == "EMERGENCY_STOP":
            logger.warning("Motion rejected: EMERGENCY STOP active.")
            return False, 0, "EMERGENCY STOP active"

        if not self.armed:
            logger.warning("Motion rejected: Robot actuators are DISARMED.")
            return False, 0, "Actuators are DISARMED (arm robot before motion)"

        target_speed = self.default_speed if speed is None else speed
        safe_speed = max(0, min(self.max_speed, target_speed))
        return True, safe_speed, None

    def forward(self, speed: Optional[int] = None) -> bool:
        valid, safe_speed, err = self._validate_motion(speed)
        if not valid:
            logger.warning(f"forward() blocked: {err}")
            return False

        self.state = "MOVING_FORWARD"
        if self.simulated:
            logger.info(f"[SIM] Moving forward at speed {safe_speed}")
        else:
            self.motor_controller.send_command(f"ROBOT_FWD {safe_speed}")
        return True

    def backward(self, speed: Optional[int] = None) -> bool:
        valid, safe_speed, err = self._validate_motion(speed)
        if not valid:
            logger.warning(f"backward() blocked: {err}")
            return False

        self.state = "MOVING_BACKWARD"
        if self.simulated:
            logger.info(f"[SIM] Moving backward at speed {safe_speed}")
        else:
            self.motor_controller.send_command(f"ROBOT_REV {safe_speed}")
        return True

    def turn_left(self, speed: Optional[int] = None) -> bool:
        valid, safe_speed, err = self._validate_motion(speed)
        if not valid:
            logger.warning(f"turn_left() blocked: {err}")
            return False

        self.state = "TURNING_LEFT"
        if self.simulated:
            logger.info(f"[SIM] Turning left at speed {safe_speed}")
        else:
            self.motor_controller.send_command(f"ROBOT_LEFT {safe_speed}")
        return True

    def turn_right(self, speed: Optional[int] = None) -> bool:
        valid, safe_speed, err = self._validate_motion(speed)
        if not valid:
            logger.warning(f"turn_right() blocked: {err}")
            return False

        self.state = "TURNING_RIGHT"
        if self.simulated:
            logger.info(f"[SIM] Turning right at speed {safe_speed}")
        else:
            self.motor_controller.send_command(f"ROBOT_RIGHT {safe_speed}")
        return True

    def stop(self) -> None:
        if self.state != "EMERGENCY_STOP":
            self.state = "STOPPED"
        if self.simulated:
            logger.info("[SIM] Stopping motors")
        else:
            self.motor_controller.send_command("ROBOT_STOP")

    def emergency_stop(self) -> None:
        """Immediate actuator cut — locks out all motion."""
        self._emergency_stopped = True
        self.armed = False
        self.state = "EMERGENCY_STOP"
        logger.critical("!!! EMERGENCY STOP ACTIVATED !!!")
        if self.simulated:
            logger.info("[SIM] Emergency stop command dispatched")
        else:
            self.motor_controller.send_command("ESTOP")

    def clear_emergency_stop(self) -> Dict[str, Any]:
        """Manually clear emergency stop lock. Actuators remain disarmed until armed."""
        self._emergency_stopped = False
        self.state = "STOPPED"
        logger.info("Emergency stop CLEARED. Robot remains DISARMED for safety.")
        return {"status": "ok", "state": self.state, "armed": self.armed}

    def set_servo(self, channel: int, angle: int) -> bool:
        """Set servo channel (0-15) to angle (0-180) only when armed.

        Servo PWM is physical motion just like a motor command.  It must obey
        the same disarmed and emergency-stop interlocks instead of bypassing
        them through a separate API path.
        """
        if not (0 <= channel <= 15):
            logger.error(f"Invalid servo channel {channel}. Must be 0-15.")
            raise ValueError(f"Servo channel must be between 0 and 15, got {channel}")

        if self._emergency_stopped or self.state == "EMERGENCY_STOP":
            logger.warning("Servo command rejected: EMERGENCY STOP active.")
            return False
        if not self.armed:
            logger.warning("Servo command rejected: Robot actuators are DISARMED.")
            return False

        angle = max(0, min(180, angle))
        pulse = int(150 + (angle / 180.0) * 450)

        if self.simulated:
            logger.info(f"[SIM] Setting servo {channel} to {angle} degrees (pulse {pulse})")
        else:
            self.servo_controller.set_pwm(channel, 0, pulse)
        return True

    @property
    def is_armed(self) -> bool:
        return self.armed

    @property
    def is_emergency_stopped(self) -> bool:
        return self._emergency_stopped

    def get_state(self) -> Dict[str, Any]:
        """Return full actuator state dictionary."""
        return {
            "state": self.state,
            "armed": self.armed,
            "emergency_stopped": self._emergency_stopped,
            "speed": self.default_speed,
            "max_speed": self.max_speed,
            "simulated": self.simulated,
            "mode": "simulation" if self.simulated else "hardware",
        }


# The production controller is created only when an action actually needs it.
# Importing a router or registering a tool must not open I2C/serial devices,
# which keeps unit tests and non-robot services from claiming physical ports.
_robot: Optional[RobotController] = None
_robot_lock = threading.RLock()


def get_robot() -> RobotController:
    """Return the process-wide robot controller, constructing it lazily."""
    global _robot
    with _robot_lock:
        if _robot is None:
            _robot = RobotController()
        return _robot


def get_existing_robot() -> Optional[RobotController]:
    """Return the existing controller without creating hardware as a side effect."""
    with _robot_lock:
        return _robot


class _LazyRobotProxy:
    """Backward-compatible proxy for legacy ``from … import robot`` users."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_robot(), name)

    def __repr__(self) -> str:
        return "<LazyRobotProxy>"


# Kept for existing callers; unlike the old module singleton it does not
# construct hardware during module import.
robot = _LazyRobotProxy()
