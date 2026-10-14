"""BaseSensor abstract class for JARVIS OS sensor architecture."""

import abc
import time
import logging
from typing import Dict, Any, Optional
from config.config_manager import config


class BaseSensor(abc.ABC):
    """
    Abstract base class for all JARVIS OS sensors.

    Attributes:
        name (str): Identifier for the sensor.
        simulation_mode (bool): Whether sensor operates in simulated mode.
        last_update (float): Unix timestamp of the last reading.
        logger (logging.Logger): Logger instance for this sensor.
    """

    def __init__(self, name: str, simulation_mode: Optional[bool] = None) -> None:
        self.name: str = name
        if simulation_mode is None:
            self.simulation_mode: bool = bool(config.get("simulation_mode", True))
        else:
            self.simulation_mode: bool = simulation_mode
        self.last_update: float = 0.0
        self.logger: logging.Logger = logging.getLogger(f"JARVIS-SENSOR-{self.name.upper()}")
        self._initialized: bool = False

        if self.simulation_mode:
            self.logger.info(f"Sensor '{self.name}' initialized in SIMULATION mode.")
        else:
            self.logger.info(f"Sensor '{self.name}' initialized in HARDWARE mode.")

    def status(self) -> str:
        """
        Returns the operational status string of the sensor.
        Returns:
            str: 'simulated' if in simulation mode, 'ready' if active, or error status.
        """
        if self.simulation_mode:
            return "simulated"
        return "ready" if self._initialized else "uninitialized"

    def calibrate(self) -> bool:
        """
        Calibrate the sensor.
        
        Returns:
            bool: True if calibration succeeded, False otherwise.
        """
        self.logger.info(f"Sensor '{self.name}' calibration invoked (simulated={self.simulation_mode}).")
        return True

    @abc.abstractmethod
    def read(self) -> Dict[str, Any]:
        """
        Read telemetry from sensor.

        Returns:
            dict: Sensor readings dictionary with 'timestamp' key.
                  Returns {'error': 'Simulated', 'timestamp': ...} when simulation_mode is True in base class.
        """
        self.last_update = time.time()
        if self.simulation_mode:
            return {"error": "Simulated", "timestamp": self.last_update}
        return {"error": "Not implemented", "timestamp": self.last_update}
