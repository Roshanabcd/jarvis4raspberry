"""JARVIS OS — Fraud Detection System package."""

from .config import FraudDetectionConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["FraudDetectionConfig", "create_router", "__version__"]
