"""Environment-driven configuration for JARVIS Real-Time Object Detection."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_OBJDET_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_object_detection" / "object_detection.db").resolve()


@dataclass(frozen=True)
class ObjectDetectionConfig:
    """Immutable runtime settings for real-time object detection, tracking, and zone alerts."""

    db_path: Path = field(default_factory=_default_db_path)
    yolo_model_path: str = field(
        default_factory=lambda: os.getenv("JARVIS_OBJDET_MODEL", "yolov8n.pt")
    )
    confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_OBJDET_CONF", "0.35"))
    )
    max_frame_bytes: int = 8 * 1024 * 1024  # 8 MB
    tracker_max_distance: float = 0.18  # Normalized frame diagonal distance
    tracker_max_disappeared: int = 12
    enable_yolo: bool = field(
        default_factory=lambda: os.getenv("JARVIS_OBJDET_ENABLE_YOLO", "1") == "1"
    )
    camera_index: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_OBJDET_CAMERA_INDEX", "0"))
    )
