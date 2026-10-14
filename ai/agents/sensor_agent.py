"""Sensor agent stub for environmental and hardware sensors."""

import json
import logging
from typing import Any, Dict, Optional
from ai.agents.base_agent import BaseAgent
from config.config_manager import config

logger = logging.getLogger("JARVIS-SENSOR-AGENT")


class SensorAgent(BaseAgent):
    """Agent stub handling sensor queries (BME280, temperature, humidity, pressure)."""

    def __init__(self):
        super().__init__(
            name="SensorAgent",
            description="Interrogates attached environmental sensors such as BME280 and temperature probes.",
        )
        self.simulation_mode = config.get("simulation_mode", True)

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process queries regarding temperature, humidity, or environmental sensors."""
        logger.info("SensorAgent handling query: '%s'", query)

        # Simulation or hardware sensor readings
        simulated_reading = {
            "sensor": "BME280",
            "temperature_c": 22.4,
            "humidity_percent": 45.8,
            "pressure_hpa": 1013.25,
            "simulated": self.simulation_mode,
        }

        q = query.lower()
        if "bme" in q:
            return (
                f"BME280 Sensor Telemetry: Temperature: {simulated_reading['temperature_c']}°C, "
                f"Humidity: {simulated_reading['humidity_percent']}%, "
                f"Pressure: {simulated_reading['pressure_hpa']} hPa. "
                f"(Simulation Mode: {self.simulation_mode})"
            )
        elif "temp" in q:
            return (
                f"Ambient temperature sensor reading: {simulated_reading['temperature_c']}°C. "
                f"Atmospheric pressure: {simulated_reading['pressure_hpa']} hPa."
            )
        else:
            return (
                f"Sensor status: All monitored channels active. "
                f"Temperature: {simulated_reading['temperature_c']}°C, "
                f"Relative Humidity: {simulated_reading['humidity_percent']}%."
            )
