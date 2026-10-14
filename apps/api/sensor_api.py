"""
JARVIS OS Sensor API Router
Exposes endpoints for querying telemetry and status of all connected sensors.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from hardware.sensors.sensor_manager import sensor_manager

sensor_router = APIRouter(prefix="/sensors", tags=["Sensors"])


@sensor_router.get("/all")
def get_all_sensors() -> Dict[str, Any]:
    """Retrieve current readings from all registered sensors."""
    return sensor_manager.read_all()


@sensor_router.get("/status")
def get_sensor_statuses() -> Dict[str, str]:
    """Retrieve operational status for all sensors."""
    return sensor_manager.status_all()


@sensor_router.get("/{name}")
def get_sensor_by_name(name: str) -> Dict[str, Any]:
    """
    Retrieve telemetry for a specific sensor by name or alias.
    Raises 404 if sensor is unknown.
    """
    sensor = sensor_manager.get_sensor(name)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"Sensor '{name}' not found")
    return sensor.read()
