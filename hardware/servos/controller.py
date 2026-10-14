"""
JARVIS Servo Controller
Wraps PCA9685 with safe angle limits, named channels, and move-with-duration.
"""
import logging
import time
from typing import Dict, Optional
from hardware.pca9685.driver import PCA9685

logger = logging.getLogger("JARVIS.Hardware.Servo")

# Standard 50Hz PWM: 1ms pulse = 0°, 2ms pulse = 180°
# At 50Hz period = 20ms, 4096 ticks/period
# 1ms = 205 ticks, 2ms = 410 ticks
_MIN_PULSE = 150   # ~0 degrees
_MAX_PULSE = 600   # ~180 degrees


class ServoChannel:
    """A single servo channel with configurable min/max angle limits."""

    def __init__(self, channel: int, min_angle: int = 0,
                 max_angle: int = 180, home_angle: int = 90) -> None:
        self.channel    = channel
        self.min_angle  = min_angle
        self.max_angle  = max_angle
        self.home_angle = home_angle
        self._current_angle: Optional[int] = None

    def _angle_to_pulse(self, angle: int) -> int:
        angle = max(self.min_angle, min(self.max_angle, angle))
        pulse = int(_MIN_PULSE + (angle / 180.0) * (_MAX_PULSE - _MIN_PULSE))
        return pulse


class ServoController:
    """
    High-level servo controller backed by PCA9685.

    SAFETY:
    - Servo power MUST come from external supply — NOT from the Raspberry Pi 5V.
    - Raspberry Pi cannot source the current required by multiple servos.
    - Verify Waveshare Servo Driver HAT B jumper/power configuration before use.
    - Default position on boot: home_angle for all configured channels.
    """

    def __init__(self, pca9685: Optional[PCA9685] = None) -> None:
        self._pca = pca9685 or PCA9685()
        self._channels: Dict[int, ServoChannel] = {}
        self._load_default_channels()
        logger.info("ServoController initialized.")

    def _load_default_channels(self) -> None:
        """Pre-configure 8 general-purpose channels with safe defaults."""
        for ch in range(8):
            self._channels[ch] = ServoChannel(
                channel=ch, min_angle=0, max_angle=180, home_angle=90
            )

    def add_channel(self, channel: int, min_angle: int = 0,
                    max_angle: int = 180, home_angle: int = 90) -> None:
        self._channels[channel] = ServoChannel(channel, min_angle, max_angle, home_angle)

    def set(self, channel: int, angle: int) -> None:
        """Set servo channel to angle (degrees). Enforces per-channel limits."""
        ch = self._channels.get(channel)
        if ch is None:
            raise ValueError(f"Servo channel {channel} not configured.")
        angle = max(ch.min_angle, min(ch.max_angle, angle))
        pulse = ch._angle_to_pulse(angle)
        self._pca.set_pwm(channel, 0, pulse)
        ch._current_angle = angle
        logger.debug(f"Servo ch{channel} → {angle}° (pulse {pulse})")

    def move(self, channel: int, target_angle: int,
             duration_ms: int = 500) -> None:
        """
        Gradually move servo from current to target angle over duration_ms.
        Prevents mechanical shock on delicate servo linkages.
        """
        ch = self._channels.get(channel)
        if ch is None:
            raise ValueError(f"Servo channel {channel} not configured.")
        start = ch._current_angle if ch._current_angle is not None else ch.home_angle
        steps = max(1, duration_ms // 20)  # ~50Hz step rate
        for i in range(1, steps + 1):
            intermediate = int(start + (target_angle - start) * i / steps)
            self.set(channel, intermediate)
            time.sleep(0.020)

    def stop(self, channel: int) -> None:
        """Release PWM signal (servo goes limp — use carefully)."""
        self._pca.set_pwm(channel, 0, 0)
        logger.debug(f"Servo ch{channel} released.")

    def home(self, channel: int) -> None:
        """Move servo to configured home angle."""
        ch = self._channels.get(channel)
        if ch:
            self.set(channel, ch.home_angle)

    def home_all(self) -> None:
        """Move all servos to home position on startup or shutdown."""
        logger.info("Homing all servos.")
        for ch_id in self._channels:
            try:
                self.home(ch_id)
                time.sleep(0.05)
            except Exception as e:
                logger.warning(f"Could not home servo ch{ch_id}: {e}")

    def status(self) -> Dict[int, dict]:
        return {
            ch_id: {"angle": ch._current_angle, "home": ch.home_angle,
                    "min": ch.min_angle, "max": ch.max_angle}
            for ch_id, ch in self._channels.items()
        }
