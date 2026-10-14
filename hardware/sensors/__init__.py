"""Sensors package for JARVIS OS."""

from hardware.sensors.base_sensor import BaseSensor
from hardware.sensors.bme280 import BME280Sensor
from hardware.sensors.bh1750 import BH1750Sensor
from hardware.sensors.vl53l0x import VL53L0XSensor
from hardware.sensors.hcsr501 import PIRSensor, HCSR501Sensor
from hardware.sensors.hcsr04 import UltrasonicSensor, HCSR04Sensor
from hardware.sensors.sensor_manager import SensorManager, sensor_manager

__all__ = [
    "BaseSensor",
    "BME280Sensor",
    "BH1750Sensor",
    "VL53L0XSensor",
    "PIRSensor",
    "HCSR501Sensor",
    "UltrasonicSensor",
    "HCSR04Sensor",
    "SensorManager",
    "sensor_manager",
]
