"""JARVIS OS — Real-Time Object Detection package."""

from .config import ObjectDetectionConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["ObjectDetectionConfig", "create_router", "__version__"]
