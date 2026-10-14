"""JARVIS Vision API"""
from fastapi import APIRouter
from config.config_manager import config

vision_router = APIRouter(prefix="/vision", tags=["vision"])

def _get_vision():
    from apps.vision.service import VisionService
    sim = config.get("simulation_mode", True)
    return VisionService(simulation=sim)

@vision_router.get("/capture")
def capture():
    vs = _get_vision()
    frame = vs.capture_frame()
    return {"status": frame.get("status", "ok"), "data": frame}

@vision_router.get("/status")
def camera_status():
    vs = _get_vision()
    return vs.camera_status()

@vision_router.get("/describe")
def describe():
    vs = _get_vision()
    return {"description": vs.describe_scene()}
