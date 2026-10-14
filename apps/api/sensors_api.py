"""FastAPI endpoints for JARVIS OS sensor suite."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from hardware.sensors.sensor_manager import sensor_manager

logger = logging.getLogger("JARVIS-API-SENSORS")

sensors_router = APIRouter(prefix="/sensors", tags=["sensors"])


@sensors_router.get("", summary="Get Sensors Overview")
@sensors_router.get("/", summary="Get Sensors Overview")
def get_sensors_overview() -> Dict[str, Any]:
    """Return overview of all registered sensors and their current status."""
    return {
        "sensors": list(sensor_manager.sensors.keys()),
        "status": sensor_manager.status_all(),
        "simulation_mode": sensor_manager.simulation_mode,
    }


@sensors_router.get("/all", summary="Read All Sensors")
def read_all_sensors() -> Dict[str, Any]:
    """
    Read telemetry from all registered sensors simultaneously.
    Returns dictionary mapping sensor name to sensor telemetry.
    """
    return sensor_manager.read_all()


@sensors_router.get("/status", summary="Get All Sensor Statuses")
def get_sensors_status() -> Dict[str, str]:
    """Retrieve operational status for all registered sensors."""
    return sensor_manager.status_all()


@sensors_router.get("/{name}", summary="Read Specific Sensor")
def read_sensor_by_name(name: str) -> Dict[str, Any]:
    """
    Read telemetry from a specific sensor by name or alias.
    Examples: 'bme280', 'bh1750', 'vl53l0x', 'hcsr501', 'hcsr04', 'pir', 'ultrasonic', 'lux'.
    """
    sensor = sensor_manager.get_sensor(name)
    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Sensor '{name}' not found. "
                f"Available sensors: {list(sensor_manager.sensors.keys())}"
            ),
        )
    return sensor.read()


@sensors_router.get("/{name}/status", summary="Get Specific Sensor Status")
def get_sensor_status_by_name(name: str) -> Dict[str, Any]:
    """Retrieve operational status for a specific sensor."""
    sensor = sensor_manager.get_sensor(name)
    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Sensor '{name}' not found. "
                f"Available sensors: {list(sensor_manager.sensors.keys())}"
            ),
        )
    return {
        "sensor": sensor.name,
        "status": sensor.status(),
        "simulation_mode": sensor.simulation_mode,
        "last_update": sensor.last_update,
    }


@sensors_router.post("/{name}/calibrate", summary="Calibrate Specific Sensor")
def calibrate_sensor(name: str) -> Dict[str, Any]:
    """Trigger calibration on a specific sensor."""
    sensor = sensor_manager.get_sensor(name)
    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor '{name}' not found.",
        )
    success = sensor.calibrate()
    return {
        "sensor": sensor.name,
        "calibrated": success,
    }
