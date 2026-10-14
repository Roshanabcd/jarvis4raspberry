"""
JARVIS Encoder Interface
Reads encoder feedback from ESP32 via serial telemetry.
GA12-N20 motors with built-in encoders.

IMPORTANT:
  Wire color mapping MUST be verified against your specific motor batch.
  Common GA12-N20 pinout: Red=Motor+, Black=Motor-, Green=Encoder A,
  White=Encoder B, Blue=VCC(3.3V), Yellow=GND — but verify with your vendor.
  Do NOT assume wire colors. Cross-reference the physical label on your motor.
"""
import logging
import time
import threading
from typing import Optional, Dict

logger = logging.getLogger("JARVIS.Hardware.Encoder")


class EncoderChannel:
    """Tracks encoder state for a single motor."""

    TICKS_PER_REV: int = 12 * 30  # 12 pulses/rev * 30:1 gearbox = 360 ticks/rev
    WHEEL_DIAMETER_MM: float = 65.0  # Adjust to your wheel size

    def __init__(self, motor_id: str) -> None:
        self.motor_id = motor_id
        self._ticks: int = 0
        self._prev_ticks: int = 0
        self._last_ts: float = time.time()
        self._rpm: float = 0.0
        self._lock = threading.Lock()

    def update(self, ticks: int) -> None:
        """Called when ESP32 sends updated tick count."""
        with self._lock:
            now = time.time()
            dt = now - self._last_ts
            delta = ticks - self._ticks
            if dt > 0:
                self._rpm = (delta / self.TICKS_PER_REV) / dt * 60.0
            self._ticks = ticks
            self._last_ts = now

    def read(self) -> Dict[str, float]:
        with self._lock:
            distance_mm = (self._ticks / self.TICKS_PER_REV) * (
                3.14159 * self.WHEEL_DIAMETER_MM
            )
            return {
                "motor_id": self.motor_id,
                "ticks": self._ticks,
                "rpm": round(self._rpm, 2),
                "distance_mm": round(distance_mm, 1),
                "timestamp": self._last_ts,
            }

    def reset(self) -> None:
        with self._lock:
            self._ticks = 0
            self._prev_ticks = 0
            self._rpm = 0.0

    def get_rpm(self) -> float:
        with self._lock:
            return self._rpm

    def get_distance(self) -> float:
        with self._lock:
            circumference = 3.14159 * self.WHEEL_DIAMETER_MM
            return (self._ticks / self.TICKS_PER_REV) * circumference

    def get_ticks(self) -> int:
        with self._lock:
            return self._ticks


class EncoderManager:
    """
    Manages encoder channels. Parses telemetry from ESP32 serial stream.
    ESP32 should send lines like: ENC LEFT 1250\n  ENC RIGHT 1248\n
    """

    def __init__(self) -> None:
        self.left  = EncoderChannel("LEFT")
        self.right = EncoderChannel("RIGHT")

    def parse_telemetry(self, line: str) -> None:
        """Called by ESP32 read thread when a line is received."""
        parts = line.strip().split()
        if len(parts) == 3 and parts[0] == "ENC":
            motor_id = parts[1].upper()
            try:
                ticks = int(parts[2])
                if motor_id == "LEFT":
                    self.left.update(ticks)
                elif motor_id == "RIGHT":
                    self.right.update(ticks)
            except ValueError:
                logger.warning(f"Invalid encoder tick value: {parts[2]}")

    def read_all(self) -> dict:
        return {"left": self.left.read(), "right": self.right.read()}

    def reset_all(self) -> None:
        self.left.reset()
        self.right.reset()
