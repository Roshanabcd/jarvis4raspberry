"""JARVIS Core Router — /api/status and /api/system"""
import time
from fastapi import APIRouter
from hardware.raspberry_pi.rpi_info import get_system_status

router = APIRouter(tags=["core"])

@router.get("/api/status")
def status():
    return {"status": "OK", "service": "JARVIS OS", "version": "0.1.0", "timestamp": time.time()}

@router.get("/api/system")
def system():
    return get_system_status()
