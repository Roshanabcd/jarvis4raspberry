"""VL53L0X Time-of-Flight (ToF) Distance Sensor driver for JARVIS OS."""

import time
from typing import Dict, Any, Optional
from hardware.sensors.base_sensor import BaseSensor


class VL53L0XSensor(BaseSensor):
    """
    VL53L0X Time-of-Flight Laser Distance Ranging Sensor.
    Measures absolute distances up to 2m in millimeters.
    In real mode, attempts to interface via the VL53L0X driver library.
    Gracefully degrades if the library or hardware is unavailable.
    """

    def __init__(
        self,
        name: str = "vl53l0x",
        i2c_bus: int = 1,
        address: int = 0x29,
        simulation_mode: Optional[bool] = None,
    ) -> None:
        super().__init__(name=name, simulation_mode=simulation_mode)
        self.bus_num = i2c_bus
        self.address = address
        self.device = None
        self._degraded = False
        self._driver_type: Optional[str] = None

        if not self.simulation_mode:
            self._init_hardware()

    def _init_hardware(self) -> None:
        """Attempt to load VL53L0X driver library and connect to sensor."""
        # Try native VL53L0X library first
        try:
            import VL53L0X

            self.device = VL53L0X.VL53L0X(i2c_bus=self.bus_num, i2c_address=self.address)
            self.device.open()
            self.device.start_ranging(VL53L0X.VL53L0X_BEST_ACCURACY_MODE)
            self._driver_type = "VL53L0X"
            self._initialized = True
            self.logger.info(f"VL53L0X ToF sensor connected via VL53L0X library at {hex(self.address)}")
            return
        except ImportError:
            self.logger.debug("VL53L0X package not found, trying adafruit_vl53l0x...")
        except Exception as e:
            self.logger.warning(f"Native VL53L0X init failed: {e}")

        # Try Adafruit CircuitPython VL53L0X library
        try:
            import board
            import busio
            import adafruit_vl53l0x

            i2c = busio.I2C(board.SCL, board.SDA)
            self.device = adafruit_vl53l0x.VL53L0X(i2c, address=self.address)
            self._driver_type = "adafruit_vl53l0x"
            self._initialized = True
            self.logger.info(f"VL53L0X connected via adafruit_vl53l0x at {hex(self.address)}")
            return
        except ImportError:
            self.logger.debug("adafruit_vl53l0x package not found.")
        except Exception as e:
            self.logger.warning(f"adafruit_vl53l0x init failed: {e}")

        # Graceful degradation
        self._degraded = True
        self.logger.warning(
            "VL53L0X hardware/library unavailable. Gracefully degrading to simulation fallback."
        )

    def status(self) -> str:
        """Returns status string including degradation indicator."""
        if self.simulation_mode:
            return "simulated"
        if self._degraded:
            return "degraded"
        return "ready" if self._initialized else "uninitialized"

    def _read_raw_hardware(self) -> int:
        """Read distance in millimeters from the physical sensor."""
        if self._driver_type == "VL53L0X" and self.device:
            distance = self.device.get_distance()
            return int(distance)
        elif self._driver_type == "adafruit_vl53l0x" and self.device:
            distance = self.device.range
            return int(distance)
        else:
            raise RuntimeError("VL53L0X driver is not active")

    def read(self) -> Dict[str, Any]:
        """
        Read distance measurement in millimeters.
        In simulation returns {'distance_mm': 250, 'timestamp': ...}.
        Gracefully handles hardware unavailability without throwing unhandled exceptions.
        """
        self.last_update = time.time()

        if self.simulation_mode or self._degraded:
            return {
                "distance_mm": 250,
                "timestamp": self.last_update,
            }

        try:
            distance = self._read_raw_hardware()
            return {
                "distance_mm": distance,
                "timestamp": self.last_update,
            }
        except Exception as e:
            self.logger.error(f"Error reading VL53L0X ToF sensor: {e}")
            return {
                "distance_mm": None,
                "error": str(e),
                "timestamp": self.last_update,
            }

    def __del__(self) -> None:
        """Clean up ranging when object is garbage collected."""
        try:
            if self._driver_type == "VL53L0X" and self.device:
                self.device.stop_ranging()
                self.device.close()
        except Exception:
            pass
