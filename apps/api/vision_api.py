"""JARVIS Vision API"""
from fastapi import APIRouter
from config.config_manager import config

vision_router = APIRouter(prefix="/vision", tags=["vision"])

def _get_vision(force_hardware: bool = False):
    from apps.vision.service import VisionService
    sim = False if force_hardware else bool(config.get("simulation_mode", True))
    return VisionService(simulation=sim)

@vision_router.get("/capture")
def capture(force_hardware: bool = False):
    vs = _get_vision(force_hardware=force_hardware)
    frame = vs.capture_frame()
    return {"status": frame.get("status", "ok"), "data": frame}

@vision_router.get("/status")
def camera_status(force_hardware: bool = False):
    vs = _get_vision(force_hardware=force_hardware)
    return vs.camera_status()

@vision_router.get("/describe")
def describe(force_hardware: bool = False):
    vs = _get_vision(force_hardware=force_hardware)
    return {"description": vs.describe_scene()}
