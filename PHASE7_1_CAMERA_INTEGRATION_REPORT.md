# JARVIS OS — Phase 7.1: Real Camera Integration, Object Detection Repair & Vision Dashboard Stabilization Report

**Branch:** `feat/jarvis-phase7-1-camera-integration`  
**Target Hardware:** Raspberry Pi 5 (8 GB RAM), Sony IMX708 (Camera Module 3 Autofocus)  
**Operating System:** Debian 13 (Trixie) ARM64 / Linux 6.12.34+rpt-rpi-2712  
**Test Suite Status:** 25 / 25 Passed (100% Green, 0 Regressions)  
**Execution Timestamp:** 2026-11-10T04:45:32Z  

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 The Hardware Conflict Problem
During Phase 7, running JARVIS photo capture or object detection triggered the following fatal hardware error:
```
ERROR: failed to acquire camera ... Device or resource busy
Pipeline handler in use by another process
```

### 1.2 Root Cause Analysis
1. **Exclusive V4L2 / libcamera Acquisition:**  
   The Raspberry Pi Camera Module 3 (Sony IMX708) connects to the Pi 5's RP1 I/O controller via MIPI CSI-2. The Linux kernel and `libcamera` enforce strict single-process exclusive ownership over `/dev/media0` and `/dev/video*`. When `/home/roshan/camera.py` initialized `Picamera2`, it locked the pipeline handler.
2. **Concurrent Hardware Access Attempt:**  
   JARVIS `tools/vision/camera_manager.py` attempted to invoke `/usr/bin/rpicam-still` or open `/dev/video0` concurrently. Because the device was already locked by `camera.py`, the kernel returned `-EBUSY` (`Device or resource busy`).
3. **RP1 CSI Controller Reset on Camera Listing:**  
   Furthermore, executing `rpicam-still --list-cameras` while `Picamera2` held active buffers triggered a hardware reset probe on the CSI bus, causing `Picamera2` to encounter `Dequeue timer of 1000000.00us has expired! Camera frontend has timed out!`.

### 1.3 Architectural Solution: Single Camera Owner Pattern
To permanently eliminate hardware contention while maintaining continuous real-time video streaming, instantaneous high-resolution snapshot capture, real-time YOLO object tracking, and Moondream VLM scene description:
- **Dedicated Camera Daemon (`camera.py`):** Acts as the **sole physical hardware owner** of the Sony IMX708 sensor using `Picamera2` on `127.0.0.1:8082`.
- **Zero-Conflict Consumer Protocol:** All other subsystems (JARVIS core API on port 8000, Web Dashboard, Moondream VLM) consume fresh frames, annotated HUD images, and telemetry via high-speed HTTP loopback endpoints (`/api/snapshot`, `/api/snapshot/annotated`, `/api/detections`, `/video_feed`).
- **Passive Hardware Probing:** `CameraManager` checks hardware availability passively through sysfs (`/sys/class/video4linux/v4l-subdev*/name` and `/sys/bus/i2c/devices/*1a/name`) and HTTP service health without ever invoking intrusive CLI probes when a stream is live.

```
+-------------------------------------------------------------------------+
|                  PHYSICAL HARDWARE: Raspberry Pi 5                      |
|                  Sony IMX708 (Camera Module 3 Autofocus)                |
|                  CSI Cable -> RP1 Controller -> /dev/media0             |
+------------------------------------+------------------------------------+
                                     | (Exclusive Hardware Ownership)
                                     v
+-------------------------------------------------------------------------+
|               DEDICATED CAMERA DAEMON: /home/roshan/camera.py           |
|  - Picamera2 (1280x720, Buffer Count: 4, Capped 15 FPS)                |
|  - Ultralytics YOLO11 NCNN (Real-time object tracking)                 |
|  - Loopback HTTP Server (127.0.0.1:8082)                                |
|  - Endpoints: /video_feed, /api/snapshot, /api/snapshot/annotated,      |
|               /api/detections, /api/health                              |
+-------------------+---------------------------------+-------------------+
                    |                                 |
                    | Loopback HTTP (Snapshots/Detections)
                    v                                 v
+------------------------------------+   +--------------------------------+
|       JARVIS CORE BACKEND          |   |       BROWSER DASHBOARD        |
|       (FastAPI: 127.0.0.1:8000)    |   |       (X11 / Chromium)         |
|  - tools/vision/camera_manager.py  |   |  - Static Web UI (Port 8000)   |
|  - apps/vision/service.py          |   |  - Toggle Live Stream / Snap   |
|  - apps/api/vision_api.py          |   |  - Monocular Distance HUD      |
|  - Saves to ~/Pictures/ (Sim: false|   |  - Full-Res Photo Viewfinder   |
+------------------------------------+   +--------------------------------+
```

---

## 2. Detailed Technical Changes

### 2.1 Updates to `/home/roshan/camera.py` (and `/home/roshan/jarvis-sample.py`)
- **Loopback Enforcement:** Added `--host` parameter defaulting strictly to `127.0.0.1`.
- **Health Telemetry Endpoint (`GET /api/health` and `GET /api/status`):**
  Returns JSON:
  ```json
  {
    "status": "ok",
    "backend": "picamera2",
    "camera": "Raspberry Pi Camera Module 3 (IMX708)",
    "fps": 10.2,
    "model": "yolo11n_ncnn_model",
    "resolution": "1280x720"
  }
  ```
- **Raw Clean Snapshot Endpoint (`GET /api/snapshot` and `GET /api/capture`):**
  Returns the latest raw, unannotated frame directly from the sensor as `image/jpeg` with headers `Content-Disposition` and `X-Capture-Timestamp`.
- **Annotated HUD Snapshot Endpoint (`GET /api/snapshot/annotated`):**
  Returns the frame with bounding boxes, labels, confidence, and radar minimap.
- **Detections Telemetry Endpoint (`GET /api/detections`):**
  Returns live detected object telemetry with distances labeled as `distance_type: "optical_monocular_estimate"`.
- **MJPEG Streaming Endpoint (`GET /video_feed`):**
  Continuous multipart MJPEG stream for real-time dashboard viewing.
- **V4L2 Queue Overflow Prevention:**
  Configured `buffer_count=4` and capped `target_fps = min(fps, 15)` when the YOLO model is active. This eliminates frame buildup and kernel dequeue timeouts.
- **NMS Optimization:**
  Passed `iou=0.45, agnostic_nms=True` to `self.model.track()`, preventing NMS timeout warnings on the ARM Cortex-A76 cores.
- **Clean Signal Handling:**
  Installed `SIGINT` and `SIGTERM` handlers that cleanly invoke `cam.stop()` and `cam.close()`, releasing `/dev/media0` immediately upon service shutdown.
- **Offline CLI Inference Mode:**
  Repaired `--test-image` and `--output-image` CLI parsing to run object detection without initializing the physical camera hardware.

### 2.2 Updates to JARVIS Backend (`jarvis-os`)

#### `tools/vision/camera_manager.py`
- Implemented **Service-First Architecture**: `capture_photo()` first queries `http://127.0.0.1:8082/api/snapshot`.
- Added image integrity verification: validates JPEG magic bytes (`\xff\xd8` and `\xff\xd9`), image dimensions (1280x720), and minimum file size (>20KB) using PIL.
- Saves clean JPEG directly to `/home/roshan/Pictures/JARVIS_Photo_YYYYMMDD_HHMMSS.jpg` with `simulated: false` and `backend: "camera_service_picamera2"`.
- Replaced intrusive `rpicam-still --list-cameras` probe in `is_camera_available()` with non-invasive passive checks:
  1. Checks if `http://127.0.0.1:8082/api/health` is responsive.
  2. Queries sysfs paths `/sys/class/video4linux/v4l-subdev*/name` and `/sys/bus/i2c/devices/*1a/name` for `imx708`.

#### `apps/vision/service.py`
- `capture_frame()`: Returns `simulated: false`, `filename`, `image_path`, and `data_b64`.
- `detect_objects()`: Synchronizes with the live camera service on port 8082 to retrieve current YOLO11 NCNN tracked targets, falling back gracefully to local OpenCV YOLOv8n ONNX inference if the service is offline.
- Every detected object explicitly includes:
  ```json
  "distance_m": 1.56,
  "distance_cm": 156,
  "distance_type": "optical_monocular_estimate",
  "optical_disclaimer": "Optical/PDAF estimate (monocular). Not for safety-critical collision avoidance."
  ```

#### `apps/api/vision_api.py`
- `POST /api/vision/capture` and `GET /api/vision/capture`: Returns `status: "ok"`, `success: true`, `simulated: false`, `filename`, and `image_url: "/api/vision/image/{filename}"`.
- Added **Protected Image Serving Endpoint** (`GET /api/vision/image/{filename}`):
  - Strictly validates filenames to eliminate Directory Traversal attacks (blocks `..`, `/`, `\`).
  - Only allows permitted extensions: `.jpg`, `.jpeg`, `.png`.
  - Ensures the resolved canonical path resides strictly inside `/home/roshan/Pictures`.
  - Serves real JPEG files with HTTP caching headers (`Last-Modified`, `ETag`, `Accept-Ranges`).
- Added `GET /api/vision/stream`: Proxies the MJPEG feed from `127.0.0.1:8082/video_feed` to dashboard clients.
- Added `GET /api/vision/detections`: Exposes current live detection telemetry.

#### `apps/dashboard/static/index.html`
- **Dual Viewfinder HUD:** Added mode switcher toggle: `[📸 Snapshot Preview]` vs `[🔴 Live Stream]`.
- **High-Resolution Photo Link:** Clicking "Capture Photo" displays the captured image preview and renders an active link: `🔍 Open Full-Res Photo (JARVIS_Photo_...)` linking to `/api/vision/image/{filename}`.
- **Structured Detection Cards:** Formats object detections with confidence percentage and **Estimated Optical Distance** (`...m / ...cm [Opt. Est]`).
- **Prominent Safety Disclaimer:**
  Displays notice: *"Optical/PDAF estimate (monocular). Not for safety-critical collision avoidance."*

---

## 3. Optical Distance Estimation Analysis & Formula

### 3.1 Pinhole Camera Distance Derivation
Monocular distance estimation computes range from target pixel height using known average object physical dimensions:
$$D = \frac{f \cdot H_{\text{real}}}{h_{\text{pixels}}}$$

Where:
- $D$: Estimated distance to the object (meters).
- $f$: Camera focal length in pixels ($f = \frac{F_{\text{mm}} \cdot H_{\text{sensor\_pixels}}}{H_{\text{sensor\_mm}}} \approx 950\text{ px}$ for Sony IMX708 at 720p).
- $H_{\text{real}}$: Assumed real-world physical height of the object class (e.g., Person $\approx 1.70\text{ m}$, Bottle $\approx 0.25\text{ m}$, Chair $\approx 0.85\text{ m}$, Laptop $\approx 0.22\text{ m}$).
- $h_{\text{pixels}}$: Detected bounding box height in pixels.

### 3.2 Limitations and Safety Disclosures
- Monocular optical estimation is subject to bounding box variance, partial occlusion, camera tilt, and object size deviations (e.g., a child vs. an adult).
- It does **not** provide ground-truth 3D depth like LiDAR or stereo vision.
- In accordance with safety guidelines, all API responses and UI cards label distance as `optical_monocular_estimate` and provide explicit warnings that it must never be used for safety-critical collision avoidance or robotics navigation.

---

## 4. Automated Test Suite Results

All test suites were executed on the Raspberry Pi 5 hardware using the Python 3.14 miniconda environment.

### 4.1 Phase 7.1 New Acceptance Suite: `tests/unit/test_phase7_1_camera_integration.py`
| Test ID | Test Name | Result | Notes |
|---|---|---|---|
| 01 | `test_01_camera_service_health` | **PASSED** | Validates HTTP 200, backend: picamera2, IMX708 |
| 02 | `test_02_camera_service_snapshot_raw_jpeg` | **PASSED** | Validates JPEG magic bytes `\xff\xd8`, 1280x720, >20KB |
| 03 | `test_03_camera_manager_service_capture` | **PASSED** | Captured to `~/Pictures/`, simulated=False |
| 04 | `test_04_jarvis_api_vision_capture_endpoint` | **PASSED** | Returns success: true, simulated: false, image_url |
| 05 | `test_05_api_image_serving_and_traversal_security` | **PASSED** | 200 for valid image; 404/400 for `../..` traversal |
| 06 | `test_06_optical_distance_labeling_and_disclaimer` | **PASSED** | distance_type: optical_monocular_estimate + disclaimer |
| 07 | `test_07_concurrent_stream_and_capture_no_device_conflict` | **PASSED** | 3 captures during active MJPEG stream without collision |

### 4.2 Full Phase 7 & 7.1 Combined Suite
```
tests/unit/test_phase7_1_camera_integration.py::TestPhase71CameraIntegration::test_01_camera_service_health PASSED
tests/unit/test_phase7_1_camera_integration.py::TestPhase71CameraIntegration::test_02_camera_service_snapshot_raw_jpeg PASSED
tests/unit/test_phase7_1_camera_integration.py::TestPhase71CameraIntegration::test_03_camera_manager_service_capture PASSED
tests/unit/test_phase7_1_camera_integration.py::TestPhase71CameraIntegration::test_04_jarvis_api_vision_capture_endpoint PASSED
tests/unit/test_phase7_1_camera_integration.py::TestPhase71CameraIntegration::test_05_api_image_serving_and_traversal_security PASSED
tests/unit/test_phase7_1_camera_integration.py::TestPhase71CameraIntegration::test_06_optical_distance_labeling_and_disclaimer PASSED
tests/unit/test_phase7_1_camera_integration.py::TestPhase71CameraIntegration::test_07_concurrent_stream_and_capture_no_device_conflict PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_01_camera_manager_singleton_and_binary PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_02_camera_manager_physical_capture_or_hardware_check PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_03_object_detector_initialization PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_04_object_detector_inference_on_image PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_05_vision_vlm_image_resizing_and_payload PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_06_vision_service_simulation_mode_truthfulness PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_07_api_vision_status_endpoint PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_08_api_vision_detect_endpoint PASSED
tests/unit/test_phase7_camera_and_vision.py::TestPhase7CameraAndVision::test_09_api_vision_describe_endpoint PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_01_face_recognition_initialization PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_02_face_recognition_encoding_and_match PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_03_user_manager_pin_hashing_and_verification PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_04_user_manager_rate_limiting_lockout PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_05_permission_manager_role_boundaries PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_06_zero_chat_privilege_escalation PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_07_audit_logging_writes_entries PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_08_api_identity_status_and_users PASSED
tests/unit/test_phase7_identity_and_roles.py::TestPhase7IdentityAndRoles::test_09_local_engine_intent_routing_and_elevation_guard PASSED

============================= 25 passed in 52.89s ==============================
```

---

## 5. Live Physical Verification

### 5.1 Real Hardware Photo Capture Test
```bash
curl -s -X POST http://127.0.0.1:8000/api/vision/capture
```
**Response:**
```json
{
  "status": "ok",
  "success": true,
  "simulated": false,
  "filename": "JARVIS_Photo_20261110_044401.jpg",
  "image_url": "/api/vision/image/JARVIS_Photo_20261110_044401.jpg",
  "width": 1280,
  "height": 720,
  "timestamp": "20261110_044401",
  "camera_model": "Sony IMX708"
}
```

### 5.2 Real Image Serving & Security Validation
```bash
curl -s -i http://127.0.0.1:8000/api/vision/image/JARVIS_Photo_20261110_044401.jpg | head -n 8
```
**Response:**
```http
HTTP/1.1 200 OK
date: Tue, 10 Nov 2026 04:44:15 GMT
server: uvicorn
content-type: image/jpeg
content-length: 234945
last-modified: Tue, 10 Nov 2026 04:44:01 GMT
etag: "ccf2dcbc7c7322d84f03d2909b5c5b12"
```

Directory Traversal Probe:
```bash
curl -s -i "http://127.0.0.1:8000/api/vision/image/..%2f..%2fetc%2fpasswd"
```
**Response:** `HTTP/1.1 404 Not Found` (Path traversal blocked).

### 5.3 Live YOLO Object Detection with Monocular Distance
```bash
curl -s -X POST http://127.0.0.1:8000/api/vision/detect
```
**Telemetry:**
```json
{
  "status": "ok",
  "success": true,
  "simulated": false,
  "count": 1,
  "objects": [
    {
      "label": "person",
      "confidence": 0.865,
      "bbox": {"x": 310, "y": 343, "width": 371, "height": 371},
      "distance_m": 1.56,
      "distance_cm": 156,
      "distance_type": "optical_monocular_estimate",
      "optical_disclaimer": "Optical/PDAF estimate (monocular). Not for safety-critical collision avoidance.",
      "zone": "NEAR"
    }
  ],
  "labels": ["person"],
  "fps": 10.4,
  "distance_type": "optical_monocular_estimate",
  "optical_disclaimer": "Optical/PDAF estimate (monocular). Not for safety-critical collision avoidance.",
  "source": "yolo11n_ncnn_service"
}
```

---

## 6. Operational Runbook

### 6.1 Starting the System
1. **Start the Dedicated Camera Daemon:**
   ```bash
   cd /home/roshan
   /home/roshan/jarvis_camera_venv/bin/python /home/roshan/camera.py --headless
   ```
2. **Verify Camera Service:**
   ```bash
   curl -s http://127.0.0.1:8082/api/health
   ```
3. **Start/Restart JARVIS Core:**
   ```bash
   sudo systemctl restart jarvis-core.service
   ```
4. **Open JARVIS Dashboard:**
   Open Google Chrome at `http://localhost:8000/dashboard`.
   Navigate to the **Vision & Identity** panel.

### 6.2 Running Automated Acceptance Tests
```bash
cd /home/roshan/.gemini/antigravity/scratch/jarvis-os
/home/roshan/miniconda3/bin/python3 -m pytest tests/unit/test_phase7_1_camera_integration.py -v
```
