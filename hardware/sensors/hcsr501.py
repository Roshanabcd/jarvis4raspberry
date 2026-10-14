"""HC-SR501 PIR Motion Detection Sensor driver for JARVIS OS.

Note:
    Connects to GPIO pin on the Raspberry Pi.
    Requires 'RPi.GPIO' or 'gpiod' library for real hardware interaction.
    On Raspberry Pi 5, the kernel uses character device GPIO (libgpiod).
"""

import time
from typing import Dict, Any, Optional
from hardware.sensors.base_sensor import BaseSensor


class PIRSensor(BaseSensor):
    """
    HC-SR501 Passive Infrared (PIR) Motion Detection Sensor.
    
    Hardware Note:
        Connects to a Raspberry Pi digital GPIO pin (default: GPIO 4 / Pin 7).
        Requires RPi.GPIO or gpiod library for hardware input reading.
    """

    def __init__(
        self,
        name: str = "hcsr501",
        pin: int = 4,
        simulation_mode: Optional[bool] = None,
    ) -> None:
        super().__init__(name=name, simulation_mode=simulation_mode)
        self.pin = pin
        self._gpio_backend: Optional[str] = None
        self._line = None
        self._chip = None

        if not self.simulation_mode:
            self._init_hardware()

    def _init_hardware(self) -> None:
        """Initialize GPIO pin using gpiod (RPi 5 standard) or RPi.GPIO."""
        # Try gpiod first (recommended for Raspberry Pi 5 / modern Linux kernel)
        try:
            import gpiod

            # Raspberry Pi 5 typically uses gpiochip4 for 40-pin header
            for chip_num in [4, 0]:
                try:
                    self._chip = gpiod.Chip(f"gpiochip{chip_num}")
                    self._line = self._chip.get_line(self.pin)
                    self._line.request(
                        consumer="JARVIS_PIR",
                        type=gpiod.LINE_REQ_DIR_IN,
                    )
                    self._gpio_backend = "gpiod"
                    self._initialized = True
                    self.logger.info(
                        f"PIRSensor initialized via gpiod on chip {chip_num}, GPIO {self.pin}"
                    )
                    return
                except Exception:
                    continue
        except ImportError:
            self.logger.debug("gpiod not available, checking RPi.GPIO...")

        # Fallback to RPi.GPIO
        try:
            import RPi.GPIO as GPIO

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self._gpio_backend = "RPi.GPIO"
            self._initialized = True
            self.logger.info(f"PIRSensor initialized via RPi.GPIO on BCM pin {self.pin}")
            return
        except ImportError:
            self.logger.debug("RPi.GPIO not available.")
        except Exception as e:
            self.logger.warning(f"RPi.GPIO setup failed: {e}")

        # Neither backend available
        self.logger.warning(
            "Neither gpiod nor RPi.GPIO could be initialized. Falling back to simulation mode."
        )
        self.simulation_mode = True

    def _read_raw_hardware(self) -> bool:
        """Read digital logic level from the PIR GPIO pin."""
        if self._gpio_backend == "gpiod" and self._line:
            val = self._line.get_value()
            return bool(val == 1)
        elif self._gpio_backend == "RPi.GPIO":
            import RPi.GPIO as GPIO

            val = GPIO.input(self.pin)
            return bool(val == GPIO.HIGH)
        raise RuntimeError("No active GPIO backend for PIR sensor")

    def read(self) -> Dict[str, Any]:
        """
        Read motion detection status.
        In simulation returns {'motion_detected': False, 'timestamp': ...}.
        """
        self.last_update = time.time()

        if self.simulation_mode:
            return {
                "motion_detected": False,
                "timestamp": self.last_update,
            }

        try:
            detected = self._read_raw_hardware()
            return {
                "motion_detected": detected,
                "timestamp": self.last_update,
            }
        except Exception as e:
            self.logger.error(f"Error reading PIR sensor on pin {self.pin}: {e}")
            return {
                "motion_detected": False,
                "error": str(e),
                "timestamp": self.last_update,
            }

    def __del__(self) -> None:
        """Release GPIO resources."""
        try:
            if self._gpio_backend == "gpiod" and self._line:
                self._line.release()
                if self._chip:
                    self._chip.close()
        except Exception:
            pass


# Alias for alternative referencing
HCSR501Sensor = PIRSensor
