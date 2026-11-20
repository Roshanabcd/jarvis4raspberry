# JARVIS OS — Real-Time Object Detection

Real-time object detection, multi-object centroid tracking, ROI intrusion zone alerts, and a live WebSocket camera HUD for **Raspberry Pi 5 (8GB)**.

## Best Features Included
- **Multi-Backend Detector (`detector.py`)**: Uses **Ultralytics YOLOv8n / YOLO11n** automatically when `ultralytics` is installed (80 COCO classes), with an ultra-fast zero-dependency offline Pillow salient-region fallback (`<10ms`) out of the box.
- **Multi-Object Centroid Tracker (`tracker.py`)**: Assigns persistent `track_id`s across frames and computes real-time velocity vectors (`velocity_x`, `velocity_y`).
- **ROI Intrusion Zones & Class Watchlists (`storage.py`, `engine.py`)**: Define custom normalized bounding boxes (`x1, y1, x2, y2`) and alert watchlists (e.g., `person`) with SQLite WAL alert logging.
- **Live Camera WebSocket HUD (`static/index.html`)**: Streams webcam / Raspberry Pi camera frames over WebSocket with real-time neon bounding boxes, track IDs, ROI zones, and live FPS telemetry.

## Quick Start (Standalone)
```bash
pip install -r requirements.txt
# Optional for full 80-class neural detection:
# pip install ultralytics
python3 -m jarvis_object_detection.app
# Open http://localhost:8027/object-detection
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_object_detection/tests -v
```
