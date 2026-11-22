"""Pydantic v1/v2 compatible schemas for JARVIS Real-Time Object Detection."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Real-Time Object Detection"
    version: str = "1.0.0"
    active_backend: str
    backends: Dict[str, bool]
    total_zones: int
    total_alerts: int


class BoundingBox(BaseModel):
    x1: float = Field(..., ge=0.0, le=1.0)
    y1: float = Field(..., ge=0.0, le=1.0)
    x2: float = Field(..., ge=0.0, le=1.0)
    y2: float = Field(..., ge=0.0, le=1.0)


class DetectedObject(BaseModel):
    track_id: int
    label: str
    confidence: float
    bbox: BoundingBox
    centroid_x: float
    centroid_y: float
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    in_zones: List[str] = Field(default_factory=list)


class DetectFrameRequest(BaseModel):
    image_base64: str = Field(..., min_length=16, max_length=12_000_000)
    confidence_threshold: Optional[float] = Field(default=None, ge=0.05, le=0.99)
    target_classes: List[str] = Field(default_factory=list)
    stream_id: str = Field(default="default", max_length=64)


class ZoneAlertRecord(BaseModel):
    id: int
    created_at: str
    zone_name: str
    label: str
    track_id: int
    confidence: float
    stream_id: str


class DetectFrameResponse(BaseModel):
    stream_id: str
    backend: str
    width: int
    height: int
    latency_ms: float
    estimated_fps: float
    object_count: int
    class_counts: Dict[str, int]
    detections: List[DetectedObject]
    triggered_alerts: List[ZoneAlertRecord]


class CreateZoneRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    x1: float = Field(..., ge=0.0, le=1.0)
    y1: float = Field(..., ge=0.0, le=1.0)
    x2: float = Field(..., ge=0.0, le=1.0)
    y2: float = Field(..., ge=0.0, le=1.0)
    watch_classes: List[str] = Field(default_factory=list)  # empty = alert on any class
    min_confidence: float = Field(default=0.35, ge=0.05, le=0.99)


class ZoneRecord(BaseModel):
    id: int
    created_at: str
    name: str
    x1: float
    y1: float
    x2: float
    y2: float
    watch_classes: List[str]
    min_confidence: float


class ZoneListResponse(BaseModel):
    total: int
    zones: List[ZoneRecord]


class AlertListResponse(BaseModel):
    total: int
    alerts: List[ZoneAlertRecord]


class AnalyticsResponse(BaseModel):
    total_frames_processed: int
    total_detections: int
    total_alerts: int
    avg_latency_ms: float
    class_distribution: Dict[str, int]
