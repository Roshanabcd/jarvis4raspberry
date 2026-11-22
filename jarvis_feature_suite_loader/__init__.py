"""JARVIS OS — Unified Feature Suite Loader (mounts all 16 additive feature modules)."""

from .loader import FEATURE_REGISTRY, mount_jarvis_feature_suite

__version__ = "1.0.0"
__all__ = ["FEATURE_REGISTRY", "mount_jarvis_feature_suite", "__version__"]
