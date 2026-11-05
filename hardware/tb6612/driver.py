"""
JARVIS TB6612FNG Motor Driver Interface
Communicates with ESP32-S3 which physically drives the TB6612FNG.
Never connects motors directly to Pi or ESP32 GPIO pins.
"""
import logging
import time
from typing import Optional
from config.config_manager import config

logger = logging.getLogger("JARVIS.Hardware.TB6612")


class MotorChannel:
    """Represents a single motor channel (A or B) on one TB6612 chip."""

    def __init__(self, channel_id: str, esp32_comm) -> None:
        self.channel_id = channel_id
        self._esp32 = esp32_comm
        self._speed: int = 0
        self._direction: str = "STOP"

    def _send(self, cmd: str) -> None:
        self._esp32.send_command(cmd)

    def forward(self, speed: int = 50) -> None:
        speed = max(0, min(100, speed))
        self._speed = speed
        self._direction = "FWD"
        self._send(f"MOTOR_{self.channel_id}_FWD {speed}")

    def reverse(self, speed: int = 50) -> None:
        speed = max(0, min(100, speed))
        self._speed = speed
        self._direction = "REV"
        self._send(f"MOTOR_{self.channel_id}_REV {speed}")

    def stop(self) -> None:
        self._speed = 0
        self._direction = "STOP"
        self._send(f"MOTOR_{self.channel_id}_STOP")

    def brake(self) -> None:
        """Active braking — different from coast stop."""
        self._speed = 0
        self._direction = "BRAKE"
        self._send(f"MOTOR_{self.channel_id}_BRAKE")

    def set_speed(self, speed: int) -> None:
        speed = max(0, min(100, speed))
        self._speed = speed
        self._send(f"MOTOR_{self.channel_id}_SPEED {speed}")

    @property
    def status(self) -> dict:
        return {"channel": self.channel_id, "speed": self._speed, "direction": self._direction}


class TB6612Controller:
    """
    High-level TB6612FNG abstraction.
    Commands are relayed to the ESP32 which handles real-time PWM.

    SAFETY:
    - Motor power comes from external 12V supply via TB6612.
    - NEVER connect motor VM to Pi GPIO or ESP32 GPIO.
    - Logic signals only on control pins.
    - Default state: all motors STOPPED.
    """

    def __init__(self, esp32_comm, ramp_ms: int = 500) -> None:
        self._esp32 = esp32_comm
        self._ramp_ms = ramp_ms
        self.simulated = config.get("simulation_mode", True)
        self.left  = MotorChannel("LEFT",  esp32_comm)
        self.right = MotorChannel("RIGHT", esp32_comm)
        self._emergency_stopped = False
        logger.info(f"TB6612Controller initialized (simulated={self.simulated}, ramp={ramp_ms}ms)")

    def _ramp(self, target_speed: int, current_speed: int,
              channel: MotorChannel, direction: str) -> None:
        """Gradual acceleration ramp to avoid mechanical shock."""
        steps = max(1, abs(target_speed - current_speed) // 10)
        for step in range(1, steps + 1):
            intermediate = current_speed + (target_speed - current_speed) * step // steps
            if direction == "FWD":
                channel.forward(intermediate)
            else:
                channel.reverse(intermediate)
            time.sleep(self._ramp_ms / 1000.0 / steps)

    def forward(self, speed: int = 50) -> None:
        if self._emergency_stopped:
            logger.warning("Cannot move: EMERGENCY STOP active.")
            return
        speed = max(0, min(100, int(speed)))
        logger.info(f"Moving FORWARD speed={speed}")
        self._esp32.send_command(f"ROBOT_FWD {speed}")

    def backward(self, speed: int = 50) -> None:
        if self._emergency_stopped:
            logger.warning("Cannot move: EMERGENCY STOP active.")
            return
        speed = max(0, min(100, int(speed)))
        logger.info(f"Moving BACKWARD speed={speed}")
        self._esp32.send_command(f"ROBOT_REV {speed}")

    def turn_left(self, speed: int = 40) -> None:
        if self._emergency_stopped:
            logger.warning("Cannot move: EMERGENCY STOP active.")
            return
        speed = max(0, min(100, int(speed)))
        self._esp32.send_command(f"ROBOT_LEFT {speed}")

    def turn_right(self, speed: int = 40) -> None:
        if self._emergency_stopped:
            logger.warning("Cannot move: EMERGENCY STOP active.")
            return
        speed = max(0, min(100, int(speed)))
        self._esp32.send_command(f"ROBOT_RIGHT {speed}")

    def stop(self) -> None:
        logger.info("Motor STOP")
        self._esp32.send_command("ROBOT_STOP")

    def brake(self) -> None:
        logger.info("Motor BRAKE")
        self._esp32.send_command("ROBOT_BRAKE")

    def emergency_stop(self) -> None:
        """Immediate motor cut — no ramp, no delay."""
        self._emergency_stopped = True
        logger.critical("!!! TB6612 EMERGENCY STOP !!!")
        self._esp32.send_command("ESTOP")

    def clear_emergency_stop(self) -> None:
        """Manually re-enable motion after e-stop is cleared."""
        self._emergency_stopped = False
        logger.info("Emergency stop cleared.")

    def rotate(self, angle_deg: int, speed: int = 40) -> None:
        """Rotate in-place by angle_deg. Positive=right, negative=left."""
        direction = "RIGHT" if angle_deg >= 0 else "LEFT"
        self._esp32.send_command(f"ROBOT_ROTATE {abs(angle_deg)} {speed} {direction}")

    def move_distance(self, distance_mm: int, speed: int = 50) -> None:
        """Move a specific distance using encoder feedback (handled by ESP32)."""
        self._esp32.send_command(f"ROBOT_DIST {distance_mm} {speed}")

    def set_wheel_speed(self, left: int, right: int) -> None:
        if self._emergency_stopped:
            return
        self._esp32.send_command(f"WHEEL_SPEED {left} {right}")

    @property
    def status(self) -> dict:
        return {
            "left": self.left.status,
            "right": self.right.status,
            "emergency_stopped": self._emergency_stopped,
        }
