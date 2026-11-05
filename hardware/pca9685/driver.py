"""
JARVIS OS PCA9685 16-Channel 12-Bit PWM Servo Driver.
Provides I2C control of the Waveshare Servo Driver HAT (B).
Features:
- Strict bounds validation on channels (0-15) and PWM values (0-4095).
- Safe error handling for I2C bus exceptions.
- Disarm and reset helpers for clean shutdown.
"""

import time
import logging
from typing import Optional
from config.config_manager import config

logger = logging.getLogger("JARVIS-PCA9685")


class PCA9685:
    """I2C driver for PCA9685 PWM controller."""

    MODE1 = 0x00
    PRESCALE = 0xFE
    LED0_ON_L = 0x06

    def __init__(self, busnum: int = 1, address: int = 0x40):
        self.address = address
        self.busnum = busnum
        self.bus = None
        self.simulated = bool(config.get("simulation_mode", True))

        if not self.simulated:
            try:
                import smbus2
                self.bus = smbus2.SMBus(busnum)
                logger.info(f"Connected to PCA9685 at I2C bus {busnum}, addr {hex(self.address)}")
                self._reset()
                self.set_pwm_freq(50)
            except Exception as e:
                logger.warning(f"Failed to initialize physical PCA9685 at {hex(self.address)}: {e}. Falling back to simulation.")
                self.simulated = True
                self.bus = None
        else:
            logger.info("PCA9685 running in SIMULATION mode.")

    def _reset(self) -> None:
        if self.simulated or not self.bus:
            return
        try:
            self.bus.write_byte_data(self.address, self.MODE1, 0x00)
        except Exception as exc:
            logger.error(f"PCA9685 reset error: {exc}")

    def set_pwm_freq(self, freq_hz: int = 50) -> None:
        """Set PWM frequency in Hz (typically 50Hz for RC servos)."""
        if self.simulated or not self.bus:
            return

        try:
            prescaleval = 25000000.0  # 25MHz internal oscillator
            prescaleval /= 4096.0     # 12-bit resolution
            prescaleval /= float(freq_hz)
            prescaleval -= 1.0
            prescale = int(prescaleval + 0.5)

            oldmode = self.bus.read_byte_data(self.address, self.MODE1)
            newmode = (oldmode & 0x7F) | 0x10  # Sleep mode to update prescale
            self.bus.write_byte_data(self.address, self.MODE1, newmode)
            self.bus.write_byte_data(self.address, self.PRESCALE, prescale)
            self.bus.write_byte_data(self.address, self.MODE1, oldmode)
            time.sleep(0.005)
            self.bus.write_byte_data(self.address, self.MODE1, oldmode | 0x80)  # Restart
        except Exception as exc:
            logger.error(f"PCA9685 set_pwm_freq error: {exc}")

    def set_pwm(self, channel: int, on: int, off: int) -> bool:
        """Set PWM duty cycle for a channel.
        channel: 0 to 15
        on: 0 to 4095
        off: 0 to 4095
        """
        if not (0 <= channel <= 15):
            raise ValueError(f"PCA9685 channel must be 0-15, got {channel}")
        on = max(0, min(4095, int(on)))
        off = max(0, min(4095, int(off)))

        if self.simulated or not self.bus:
            logger.debug(f"[SIM-PCA] Channel {channel} -> on: {on}, off: {off}")
            return True

        try:
            reg_base = self.LED0_ON_L + 4 * channel
            self.bus.write_byte_data(self.address, reg_base, on & 0xFF)
            self.bus.write_byte_data(self.address, reg_base + 1, on >> 8)
            self.bus.write_byte_data(self.address, reg_base + 2, off & 0xFF)
            self.bus.write_byte_data(self.address, reg_base + 3, off >> 8)
            return True
        except Exception as exc:
            logger.error(f"PCA9685 write error on ch {channel}: {exc}")
            return False

    def stop_channel(self, channel: int) -> bool:
        """Turn off PWM signal on a channel (servo released)."""
        return self.set_pwm(channel, 0, 0)

    def stop_all(self) -> None:
        """Release PWM on all 16 channels."""
        for ch in range(16):
            self.stop_channel(ch)

    def close(self) -> None:
        """Cleanly close I2C bus."""
        self.stop_all()
        if self.bus:
            try:
                self.bus.close()
            except Exception:
                pass
            self.bus = None
