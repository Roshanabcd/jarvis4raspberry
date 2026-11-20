"""Core Real-Time Object Detection engine combining detection, tracking, ROI zones, and alerts."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from .config import ObjectDetectionConfig
from .detector import MultiBackendDetector, decode_frame
from .models import (
    AlertListResponse,
    AnalyticsResponse,
    BoundingBox,
    CreateZoneRequest,
    DetectFrameRequest,
    DetectFrameResponse,
    DetectedObject,
    HealthResponse,
    ZoneAlertRecord,
    ZoneListResponse,
    ZoneRecord,
)
from .storage import ObjectDetectionStore
from .tracker import CentroidTracker


class ObjectDetectionEngine:
    """Coordinates frame detection, per-stream centroid tracking, ROI zone alerting, and analytics."""

    def __init__(self, config: Optional[ObjectDetectionConfig] = None) -> None:
        self.config = config or ObjectDetectionConfig()
        self.store = ObjectDetectionStore(self.config.db_path)
        self.detector = MultiBackendDetector(self.config)
        self._trackers: Dict[str, CentroidTracker] = {}

    def _tracker_for(self, stream_id: str) -> CentroidTracker:
        if stream_id not in self._trackers:
            self._trackers[stream_id] = CentroidTracker(
                max_distance=self.config.tracker_max_distance,
                max_disappeared=self.config.tracker_max_disappeared,
            )
        return self._trackers[stream_id]

    def health(self) -> HealthResponse:
        an = self.store.analytics()
        return HealthResponse(
            active_backend=self.detector.active_backend_name(),
            backends=self.detector.available_backends(),
            total_zones=an["total_zones"],
            total_alerts=an["total_alerts"],
        )

    def upsert_zone(self, req: CreateZoneRequest) -> ZoneRecord:
        if req.x2 <= req.x1 or req.y2 <= req.y1:
            raise ValueError("Zone coordinates must satisfy x2 > x1 and y2 > y1.")
        watch = [c.strip().lower() for c in req.watch_classes if c.strip()]
        saved = self.store.upsert_zone(
            name=req.name.strip(),
            x1=req.x1,
            y1=req.y1,
            x2=req.x2,
            y2=req.y2,
            watch_classes=watch,
            min_confidence=req.min_confidence,
        )
        return ZoneRecord(**saved)

    def list_zones(self) -> ZoneListResponse:
        zones = [ZoneRecord(**z) for z in self.store.list_zones()]
        return ZoneListResponse(total=len(zones), zones=zones)

    def delete_zone(self, zone_id: int) -> bool:
        return self.store.delete_zone(zone_id)

    def detect_frame(self, req: DetectFrameRequest) -> DetectFrameResponse:
        t0 = time.perf_counter()
        img_bytes = decode_frame(req.image_base64, max_bytes=self.config.max_frame_bytes)
        conf = req.confidence_threshold if req.confidence_threshold is not None else self.config.confidence_threshold

        backend, width, height, raw_dets = self.detector.detect(img_bytes, conf_thresh=conf)

        if req.target_classes:
            allowed = {c.strip().lower() for c in req.target_classes if c.strip()}
            raw_dets = [d for d in raw_dets if str(d["label"]).lower() in allowed]

        stream_id = req.stream_id.strip() or "default"
        tracked = self._tracker_for(stream_id).update(raw_dets)
        zones = self.store.list_zones()

        detections: List[DetectedObject] = []
        class_counts: Dict[str, int] = {}
        triggered_alerts: List[ZoneAlertRecord] = []

        for obj in tracked:
            lbl = str(obj["label"])
            class_counts[lbl] = class_counts.get(lbl, 0) + 1
            cx, cy = float(obj["centroid_x"]), float(obj["centroid_y"])
            in_zones: List[str] = []

            for z in zones:
                if z["x1"] <= cx <= z["x2"] and z["y1"] <= cy <= z["y2"]:
                    in_zones.append(z["name"])
                    watch = z["watch_classes"]
                    if (not watch or lbl.lower() in watch) and float(obj["confidence"]) >= float(z["min_confidence"]):
                        alert_row = self.store.log_alert(
                            zone_name=z["name"],
                            label=lbl,
                            track_id=int(obj["track_id"]),
                            confidence=float(obj["confidence"]),
                            stream_id=stream_id,
                        )
                        triggered_alerts.append(ZoneAlertRecord(**alert_row))

            detections.append(
                DetectedObject(
                    track_id=int(obj["track_id"]),
                    label=lbl,
                    confidence=float(obj["confidence"]),
                    bbox=BoundingBox(x1=obj["x1"], y1=obj["y1"], x2=obj["x2"], y2=obj["y2"]),
                    centroid_x=cx,
                    centroid_y=cy,
                    velocity_x=float(obj["velocity_x"]),
                    velocity_y=float(obj["velocity_y"]),
                    in_zones=in_zones,
                )
            )

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        est_fps = round(1000.0 / max(latency_ms, 1.0), 1)
        self.store.log_frame(
            stream_id=stream_id,
            backend=backend,
            object_count=len(detections),
            class_counts=class_counts,
            latency_ms=latency_ms,
        )

        return DetectFrameResponse(
            stream_id=stream_id,
            backend=backend,
            width=width,
            height=height,
            latency_ms=latency_ms,
            estimated_fps=est_fps,
            object_count=len(detections),
            class_counts=class_counts,
            detections=detections,
            triggered_alerts=triggered_alerts,
        )

    def list_alerts(self, limit: int = 50) -> AlertListResponse:
        alerts = [ZoneAlertRecord(**a) for a in self.store.list_alerts(limit=limit)]
        return AlertListResponse(total=len(alerts), alerts=alerts)

    def analytics(self) -> AnalyticsResponse:
        an = self.store.analytics()
        return AnalyticsResponse(
            total_frames_processed=an["total_frames_processed"],
            total_detections=an["total_detections"],
            total_alerts=an["total_alerts"],
            avg_latency_ms=an["avg_latency_ms"],
            class_distribution=an["class_distribution"],
        )
