# Integrating Real-Time Object Detection into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy `jarvis_object_detection/` into your JARVIS OS repository (e.g. `~/.gemini/antigravity/scratch/jarvis-os/jarvis_object_detection/`).

## 2. Mount the Router in Your JARVIS FastAPI App
```python
from jarvis_object_detection import ObjectDetectionConfig, create_router

app.include_router(create_router(ObjectDetectionConfig()))
```

## 3. Environment Variables (Optional)
- `JARVIS_OBJDET_DB_PATH`: SQLite WAL database path (default: `.jarvis_object_detection/object_detection.db`).
- `JARVIS_OBJDET_MODEL`: Ultralytics YOLO weights path (default: `yolov8n.pt`, or export to NCNN for fastest Pi 5 CPU FPS).
- `JARVIS_OBJDET_CONF`: Default confidence threshold (default: `0.35`).
- `JARVIS_OBJDET_ENABLE_YOLO`: Set `1` to use Ultralytics YOLO when installed, `0` for offline salient-region mode.
- `JARVIS_OBJDET_PORT`: Standalone server port (default: `8027`).

## 4. Endpoints Added
- `GET /object-detection` — Live Camera WebSocket HUD, Image Upload, ROI Zone Editor, and Analytics
- `GET /api/object-detection/health` — Active detector backend, zones, and alert counts
- `POST /api/object-detection/detect` — Single-frame detection + centroid tracking
- `WS /api/object-detection/ws/stream` — Real-time WebSocket frame streaming
- `POST /api/object-detection/zones`, `GET /api/object-detection/zones`, `DELETE /api/object-detection/zones/{id}` — ROI intrusion zone management
- `GET /api/object-detection/alerts` & `GET /api/object-detection/analytics` — Triggered alerts and class/FPS telemetry
