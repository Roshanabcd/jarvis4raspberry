"""SensorManager orchestrator for JARVIS OS hardware and simulated sensors."""

import time
import logging
from typing import Dict, Optional, Any
from config.config_manager import config
from hardware.sensors.base_sensor import BaseSensor
from hardware.sensors.bme280 import BME280Sensor
from hardware.sensors.bh1750 import BH1750Sensor
from hardware.sensors.vl53l0x import VL53L0XSensor
from hardware.sensors.hcsr501 import PIRSensor
from hardware.sensors.hcsr04 import UltrasonicSensor


class SensorManager:
    """
    Central manager for all JARVIS OS sensors.
    
    Attributes:
        sensors (Dict[str, BaseSensor]): Mapping of sensor names to sensor instances.
        simulation_mode (bool): Global simulation setting.
    """

    def __init__(self, simulation_mode: Optional[bool] = None) -> None:
        self.logger = logging.getLogger("JARVIS-SENSOR-MANAGER")
        if simulation_mode is None:
            self.simulation_mode = bool(config.get("simulation_mode", True))
        else:
            self.simulation_mode = simulation_mode

        self.sensors: Dict[str, BaseSensor] = {}
        self._aliases: Dict[str, str] = {
            "pir": "hcsr501",
            "motion": "hcsr501",
            "ultrasonic": "hcsr04",
            "sonar": "hcsr04",
            "distance": "vl53l0x",
            "tof": "vl53l0x",
            "light": "bh1750",
            "lux": "bh1750",
            "temp": "bme280",
            "weather": "bme280",
            "barometer": "bme280",
        }
        self._initialize_sensors()

    def _initialize_sensors(self) -> None:
        """Instantiate and register all supported sensors."""
        self.logger.info(
            f"Initializing sensor suite (simulation_mode={self.simulation_mode})..."
        )

        try:
            self.sensors["bme280"] = BME280Sensor(simulation_mode=self.simulation_mode)
        except Exception as e:
            self.logger.error(f"Failed to instantiate BME280Sensor: {e}")

        try:
            self.sensors["bh1750"] = BH1750Sensor(simulation_mode=self.simulation_mode)
        except Exception as e:
            self.logger.error(f"Failed to instantiate BH1750Sensor: {e}")

        try:
            self.sensors["vl53l0x"] = VL53L0XSensor(simulation_mode=self.simulation_mode)
        except Exception as e:
            self.logger.error(f"Failed to instantiate VL53L0XSensor: {e}")

        try:
            self.sensors["hcsr501"] = PIRSensor(simulation_mode=self.simulation_mode)
        except Exception as e:
            self.logger.error(f"Failed to instantiate PIRSensor: {e}")

        try:
            self.sensors["hcsr04"] = UltrasonicSensor(simulation_mode=self.simulation_mode)
        except Exception as e:
            self.logger.error(f"Failed to instantiate UltrasonicSensor: {e}")

        self.logger.info(
            f"Sensor suite initialized with {len(self.sensors)} sensors: {list(self.sensors.keys())}"
        )

    def get_sensor(self, name: str) -> Optional[BaseSensor]:
        """
        Retrieve a sensor instance by name or alias (case-insensitive).

        Args:
            name (str): Sensor name (e.g. 'bme280', 'hcsr04', 'pir', 'lux').

        Returns:
            Optional[BaseSensor]: Sensor instance if found, None otherwise.
        """
        normalized_name = name.strip().lower()

        # Direct match
        if normalized_name in self.sensors:
            return self.sensors[normalized_name]

        # Alias lookup
        if normalized_name in self._aliases:
            canonical_name = self._aliases[normalized_name]
            return self.sensors.get(canonical_name)

        return None

    def read_all(self) -> Dict[str, Any]:
        """
        Poll and read data from all registered sensors.
        Catches errors per sensor so that a single failure doesn't halt the pipeline.

        Returns:
            Dict[str, Any]: Mapping of sensor names to their telemetry dictionaries.
        """
        results: Dict[str, Any] = {}
        for name, sensor in self.sensors.items():
            try:
                results[name] = sensor.read()
            except Exception as e:
                self.logger.error(f"Unhandled exception reading sensor '{name}': {e}")
                results[name] = {
                    "error": str(e),
                    "timestamp": time.time(),
                }
        return results

    def status_all(self) -> Dict[str, str]:
        """
        Retrieve operational status for each sensor.

        Returns:
            Dict[str, str]: Mapping of sensor names to their status strings.
        """
        statuses: Dict[str, str] = {}
        for name, sensor in self.sensors.items():
            try:
                statuses[name] = sensor.status()
            except Exception as e:
                self.logger.error(f"Error querying status for '{name}': {e}")
                statuses[name] = f"error: {e}"
        return statuses

    def calibrate_all(self) -> Dict[str, bool]:
        """
        Trigger calibration across all eligible sensors.

        Returns:
            Dict[str, bool]: Mapping of sensor names to calibration success flags.
        """
        calibration_results: Dict[str, bool] = {}
        for name, sensor in self.sensors.items():
            try:
                calibration_results[name] = sensor.calibrate()
            except Exception as e:
                self.logger.error(f"Error calibrating '{name}': {e}")
                calibration_results[name] = False
        return calibration_results


# Default global instance
sensor_manager = SensorManager()
