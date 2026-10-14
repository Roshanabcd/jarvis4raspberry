"""HC-SR04 Ultrasonic Distance Sensor driver for JARVIS OS.

CRITICAL HARDWARE WARNING:
    The HC-SR04 ECHO pin outputs a 5V TTL logic level!
    NEVER connect the ECHO pin directly to a Raspberry Pi GPIO pin.
    Raspberry Pi GPIO pins are rated for 3.3V maximum; connecting 5V directly
    can cause irreversible damage to the SoC GPIO bank.
    Always use a voltage divider (e.g., 1kΩ and 2kΩ resistors) or a bidirectional
    logic level converter to safely step down the 5V ECHO signal to ~3.3V.
"""

import time
from typing import Dict, Any, Optional
from hardware.sensors.base_sensor import BaseSensor


class UltrasonicSensor(BaseSensor):
    """
    HC-SR04 Ultrasonic Distance Sensor.
    
    WARNING:
        HC-SR04 ECHO pin outputs 5V — NEVER connect directly to Pi GPIO. Use voltage divider.
    """

    def __init__(
        self,
        name: str = "hcsr04",
        trig_pin: int = 23,
        echo_pin: int = 24,
        simulation_mode: Optional[bool] = None,
    ) -> None:
        super().__init__(name=name, simulation_mode=simulation_mode)
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self._gpio_backend: Optional[str] = None
        self._trig_line = None
        self._echo_line = None
        self._chip = None

        if not self.simulation_mode:
            self._init_hardware()

    def _init_hardware(self) -> None:
        """Initialize GPIO for Trigger (OUT) and Echo (IN)."""
        # Try gpiod first (RPi 5 standard)
        try:
            import gpiod

            for chip_num in [4, 0]:
                try:
                    self._chip = gpiod.Chip(f"gpiochip{chip_num}")
                    self._trig_line = self._chip.get_line(self.trig_pin)
                    self._trig_line.request(
                        consumer="JARVIS_TRIG",
                        type=gpiod.LINE_REQ_DIR_OUT,
                        default_val=0,
                    )
                    self._echo_line = self._chip.get_line(self.echo_pin)
                    self._echo_line.request(
                        consumer="JARVIS_ECHO",
                        type=gpiod.LINE_REQ_DIR_IN,
                    )
                    self._gpio_backend = "gpiod"
                    self._initialized = True
                    self.logger.info(
                        f"UltrasonicSensor initialized via gpiod on chip {chip_num} "
                        f"(TRIG={self.trig_pin}, ECHO={self.echo_pin})"
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
            GPIO.setup(self.trig_pin, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.echo_pin, GPIO.IN)
            self._gpio_backend = "RPi.GPIO"
            self._initialized = True
            self.logger.info(
                f"UltrasonicSensor initialized via RPi.GPIO (TRIG={self.trig_pin}, ECHO={self.echo_pin})"
            )
            return
        except ImportError:
            self.logger.debug("RPi.GPIO not available.")
        except Exception as e:
            self.logger.warning(f"RPi.GPIO setup failed: {e}")

        self.logger.warning(
            "Neither gpiod nor RPi.GPIO could be initialized. Falling back to simulation mode."
        )
        self.simulation_mode = True

    def _measure_distance_hardware(self) -> float:
        """Send trigger pulse and measure pulse duration on Echo pin."""
        timeout_sec = 0.04  # 40ms max wait (~6.8m roundtrip limit)

        if self._gpio_backend == "gpiod":
            # Ensure trigger is low
            self._trig_line.set_value(0)
            time.sleep(0.000002)

            # 10us trigger pulse
            self._trig_line.set_value(1)
            time.sleep(0.000010)
            self._trig_line.set_value(0)

            # Wait for echo to go HIGH
            start_wait = time.perf_counter()
            while self._echo_line.get_value() == 0:
                pulse_start = time.perf_counter()
                if pulse_start - start_wait > timeout_sec:
                    raise TimeoutError("Timed out waiting for ECHO pulse to start")

            # Wait for echo to go LOW
            while self._echo_line.get_value() == 1:
                pulse_end = time.perf_counter()
                if pulse_end - pulse_start > timeout_sec:
                    raise TimeoutError("Timed out waiting for ECHO pulse to end")

        elif self._gpio_backend == "RPi.GPIO":
            import RPi.GPIO as GPIO

            # Ensure trigger is low
            GPIO.output(self.trig_pin, GPIO.LOW)
            time.sleep(0.000002)

            # 10us trigger pulse
            GPIO.output(self.trig_pin, GPIO.HIGH)
            time.sleep(0.000010)
            GPIO.output(self.trig_pin, GPIO.LOW)

            # Wait for echo to go HIGH
            start_wait = time.perf_counter()
            while GPIO.input(self.echo_pin) == GPIO.LOW:
                pulse_start = time.perf_counter()
                if pulse_start - start_wait > timeout_sec:
                    raise TimeoutError("Timed out waiting for ECHO pulse to start")

            # Wait for echo to go LOW
            while GPIO.input(self.echo_pin) == GPIO.HIGH:
                pulse_end = time.perf_counter()
                if pulse_end - pulse_start > timeout_sec:
                    raise TimeoutError("Timed out waiting for ECHO pulse to end")
        else:
            raise RuntimeError("No GPIO backend available for distance measurement")

        pulse_duration = pulse_end - pulse_start
        # Speed of sound is 34300 cm/s; divide by 2 for roundtrip
        distance = (pulse_duration * 34300.0) / 2.0
        return round(distance, 2)

    def read(self) -> Dict[str, Any]:
        """
        Read distance in centimeters.
        In simulation returns {'distance_cm': 45.0, 'timestamp': ...}.
        """
        self.last_update = time.time()

        if self.simulation_mode:
            return {
                "distance_cm": 45.0,
                "timestamp": self.last_update,
            }

        try:
            distance = self._measure_distance_hardware()
            return {
                "distance_cm": distance,
                "timestamp": self.last_update,
            }
        except Exception as e:
            self.logger.error(f"Error measuring ultrasonic distance: {e}")
            return {
                "distance_cm": None,
                "error": str(e),
                "timestamp": self.last_update,
            }

    def __del__(self) -> None:
        """Clean up GPIO resources."""
        try:
            if self._gpio_backend == "gpiod":
                if self._trig_line:
                    self._trig_line.release()
                if self._echo_line:
                    self._echo_line.release()
                if self._chip:
                    self._chip.close()
        except Exception:
            pass


# Provide HCSR04Sensor alias
HCSR04Sensor = UltrasonicSensor
