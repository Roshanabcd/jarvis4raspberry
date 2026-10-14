"""
JARVIS OS - Diagnostics and Hardware Health API
Exposes endpoints for system diagnostics, hardware health, I2C scan, and serial bus discovery.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from hardware.raspberry_pi.diagnostics import Diagnostics
from hardware.raspberry_pi.health_monitor import HealthMonitor

logger = logging.getLogger("JARVIS.API.Diagnostics")

diagnostics_router = APIRouter(tags=["Diagnostics & Health"])
diag_router = diagnostics_router
_diagnostics = Diagnostics()
_health_monitor = HealthMonitor()


@diagnostics_router.get("/diagnostics", summary="Run full system diagnostics")
async def get_diagnostics() -> Dict[str, Any]:
    """
    Executes all system diagnostics: Python version, Node.js runtime, storage,
    network connectivity, I2C bus, serial ports, simulation mode, database access,
    and configuration loading. Returns a structured pass/fail report.
    """
    try:
        report = _diagnostics.run_full_diagnostics()
        return report
    except Exception as exc:
        logger.error("Error executing system diagnostics: %s", exc)
        raise HTTPException(status_code=500, detail=f"Diagnostics failed: {exc}")


@diagnostics_router.get("/health", summary="Hardware and system health status")
async def get_health() -> Dict[str, Any]:
    """
    Returns full hardware health metrics including CPU, RAM, temperature,
    disk usage, I2C devices, serial ports, audio subsystem, and network state.
    """
    try:
        health_data = _health_monitor.check_all()
        return health_data
    except Exception as exc:
        logger.error("Error retrieving hardware health: %s", exc)
        raise HTTPException(status_code=500, detail=f"Health check failed: {exc}")


@diagnostics_router.get("/health/i2c", summary="Scan I2C bus for devices")
async def get_i2c_health() -> Dict[str, Any]:
    """
    Lists available /dev/i2c-* buses and queries detected addresses using i2cdetect.
    """
    try:
        return _health_monitor.check_i2c()
    except Exception as exc:
        logger.error("Error checking I2C health: %s", exc)
        raise HTTPException(status_code=500, detail=f"I2C scan failed: {exc}")


@diagnostics_router.get("/health/serial", summary="Scan serial ports")
async def get_serial_health() -> Dict[str, Any]:
    """
    Discovers connected serial interfaces matching /dev/ttyUSB*, /dev/ttyACM*, /dev/ttyAMA*.
    """
    try:
        return _health_monitor.check_serial()
    except Exception as exc:
        logger.error("Error checking serial ports: %s", exc)
        raise HTTPException(status_code=500, detail=f"Serial check failed: {exc}")
