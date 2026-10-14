"""JARVIS Health API — GET /api/health"""
import logging
from fastapi import APIRouter

logger = logging.getLogger("JARVIS.API.Health")
health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.get("")
def health_check():
    components = {}
    # DB
    try:
        from memory.long_term.database import db
        db.summarize()
        components["db"] = "OK"
    except Exception as e:
        components["db"] = f"ERROR: {e}"
    # Config
    try:
        from config.config_manager import config
        _ = config.get("api_port", 8000)
        components["config"] = "OK"
    except Exception as e:
        components["config"] = f"ERROR: {e}"
    # Robot
    try:
        from tools.robotics.controller import robot
        components["robot"] = robot.state if hasattr(robot, "state") else "OK"
    except Exception as e:
        components["robot"] = f"ERROR: {e}"
    # Sensors
    try:
        from hardware.sensors.sensor_manager import sensor_manager
        statuses = sensor_manager.status_all()
        any_err = any("ERROR" in str(v).upper() for v in statuses.values())
        components["sensors"] = "WARNING" if any_err else "OK"
    except Exception as e:
        components["sensors"] = f"ERROR: {e}"
    # AI
    try:
        from ai.router.model_router import ModelRouter
        router = ModelRouter()
        status = router.get_status()
        any_avail = any(v for v in status.get("providers", {}).values())
        components["ai"] = "OK" if any_avail else "OFFLINE"
    except Exception as e:
        components["ai"] = f"OFFLINE: {e}"

    overall = "OK"
    for v in components.values():
        if "ERROR" in str(v).upper():
            overall = "ERROR"; break
        if "WARNING" in str(v).upper() or "OFFLINE" in str(v).upper():
            overall = "WARNING"

    return {"status": overall, "components": components}

@health_router.get("/i2c")
def i2c_scan():
    from hardware.raspberry_pi.rpi_info import list_i2c_devices, scan_i2c_bus
    buses = list_i2c_devices()
    results = {}
    for bus_path in buses:
        try:
            bus_num = int(bus_path.split("-")[-1])
            results[bus_path] = scan_i2c_bus(bus_num)
        except Exception as e:
            results[bus_path] = [f"Error: {e}"]
    return {"buses": buses, "devices": results}

@health_router.get("/serial")
def serial_ports():
    from hardware.raspberry_pi.rpi_info import list_serial_ports
    return {"ports": list_serial_ports()}
