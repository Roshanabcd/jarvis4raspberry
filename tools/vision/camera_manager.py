"""
JARVIS OS — Central Camera Manager.
Controls physical capture from Raspberry Pi Camera Module 3 (Sony IMX708).

Enforces:
- Single-instance camera hardware locking (mutex)
- Real image validation (file existence, non-zero size, JPEG header, dimension integrity)
- Standard image storage under /home/roshan/Pictures with timestamped filenames
- Zero mock / simulation fallbacks: actual physical capture or explicit error
"""

import datetime
import json
import logging
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

logger = logging.getLogger("JARVIS.Vision.CameraManager")

PICTURES_DIR = Path("/home/roshan/Pictures")
PICTURES_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_CAMERA_SERVICE_URL = "http://127.0.0.1:8082"


class CameraManager:
    """Central singleton controller for Sony IMX708 camera on Raspberry Pi 5."""

    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._lock = threading.Lock()
        self._is_capturing = False
        self._last_capture_time: Optional[float] = None
        self._last_image_path: Optional[str] = None
        self._last_metadata: Dict[str, Any] = {}
        self._camera_model = "Sony IMX708 (Camera Module 3)"
        self._cli_binary = self._detect_cli_binary()
        self._initialized = True
        logger.info("CameraManager initialized (binary=%s, model=%s)", self._cli_binary, self._camera_model)

    def _detect_cli_binary(self) -> Optional[str]:
        """Detect the supported native Raspberry Pi camera CLI utility."""
        for candidate in ["rpicam-still", "libcamera-still", "rpicam-jpeg"]:
            path = shutil.which(candidate)
            if path:
                return path
        return None

    def get_service_url(self) -> str:
        """Resolve the active loopback camera service URL."""
        descriptor_path = Path("/tmp/jarvis_camera_service.json")
        if descriptor_path.exists():
            try:
                with open(descriptor_path, "r") as f:
                    data = json.load(f)
                port = data.get("port", 8082)
                host = data.get("host", "127.0.0.1")
                return f"http://{host}:{port}"
            except Exception:
                pass
        return DEFAULT_CAMERA_SERVICE_URL

    def is_service_running(self) -> bool:
        """Check if the dedicated camera vision service is running on loopback."""
        url = self.get_service_url()
        try:
            r = requests.get(f"{url}/api/health", timeout=0.6)
            if r.status_code == 200:
                data = r.json()
                return data.get("status") == "ok"
        except Exception:
            pass
        return False

    def get_service_health(self) -> Optional[Dict[str, Any]]:
        """Fetch current telemetry and health status from camera service."""
        url = self.get_service_url()
        try:
            r = requests.get(f"{url}/api/health", timeout=0.8)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def get_service_status(self) -> Optional[Dict[str, Any]]:
        """Alias for get_service_health."""
        return self.get_service_health()

    def is_camera_available(self) -> bool:
        """Verify camera is available either via active vision service or kernel hardware sysfs (non-invasive)."""
        if self.is_service_running():
            return True
        # Passive non-invasive sysfs check (does not reset sensor or disrupt active streams)
        for dev_path in Path("/sys/class/video4linux").glob("v4l-subdev*"):
            try:
                name_file = dev_path / "name"
                if name_file.exists() and "imx708" in name_file.read_text().lower():
                    return True
            except Exception:
                pass
        for i2c_path in Path("/sys/bus/i2c/devices").glob("*1a"):
            try:
                name_file = i2c_path / "name"
                if name_file.exists() and "imx708" in name_file.read_text().lower():
                    return True
            except Exception:
                pass
        # Only as a fallback if sysfs did not detect it
        if not self._cli_binary:
            return False
        try:
            res = subprocess.run(
                [self._cli_binary, "--list-cameras"],
                capture_output=True,
                text=True,
                timeout=3.0,
                check=False,
            )
            return res.returncode == 0 and ("imx708" in res.stdout.lower() or "available cameras" in res.stdout.lower())
        except Exception as e:
            logger.debug("Camera availability check error: %s", e)
            return False

    def get_status(self) -> Dict[str, Any]:
        """Return truthful hardware and service status dictionary."""
        svc_running = self.is_service_running()
        svc_health = self.get_service_health() if svc_running else None
        available = svc_running or self.is_camera_available()
        return {
            "available": available,
            "camera_model": self._camera_model,
            "binary": self._cli_binary,
            "service_active": svc_running,
            "service_url": self.get_service_url() if svc_running else None,
            "service_telemetry": svc_health,
            "backend": "camera_service_picamera2" if svc_running else (self._cli_binary or "unavailable"),
            "is_capturing": self._is_capturing,
            "last_capture_time": self._last_capture_time,
            "last_image_path": self._last_image_path,
            "last_metadata": self._last_metadata,
            "save_directory": str(PICTURES_DIR),
        }

    def _capture_from_service(self, target_path: Path, width: int = 1280, height: int = 720) -> Dict[str, Any]:
        """Capture a fresh real photo by requesting snapshot from the running camera service."""
        url = self.get_service_url()
        t0 = time.perf_counter()
        logger.info("Requesting fresh frame snapshot from camera service: %s/api/snapshot", url)

        try:
            r = requests.get(f"{url}/api/snapshot", timeout=6.0)
            elapsed_s = round(time.perf_counter() - t0, 3)

            if r.status_code != 200 or not r.content:
                err_msg = f"Camera service HTTP {r.status_code}: {r.text[:120]}"
                logger.error("Camera service snapshot failed: %s", err_msg)
                return {
                    "success": False,
                    "simulated": False,
                    "error": err_msg,
                    "image_path": None,
                    "duration_s": elapsed_s,
                }

            with open(target_path, "wb") as f:
                f.write(r.content)

            # Thorough validation of the output file
            val_ok, val_err, img_info = self._validate_image_file(target_path)
            if not val_ok:
                logger.error("Captured snapshot validation failed: %s", val_err)
                target_path.unlink(missing_ok=True)
                return {
                    "success": False,
                    "simulated": False,
                    "error": f"Captured snapshot failed validation: {val_err}",
                    "image_path": None,
                }

            self._last_capture_time = time.time()
            self._last_image_path = str(target_path)
            self._last_metadata = {
                "filename": target_path.name,
                "path": str(target_path),
                "width": img_info.get("width", width),
                "height": img_info.get("height", height),
                "size_bytes": img_info.get("size_bytes", len(r.content)),
                "timestamp": self._last_capture_time,
                "camera_model": self._camera_model,
                "backend": "camera_service_picamera2",
                "simulated": False,
                "duration_s": elapsed_s,
            }

            logger.info("✓ Real camera service capture verified: %s (%dx%d, %d bytes, %.2fs)",
                        target_path.name, self._last_metadata["width"],
                        self._last_metadata["height"], self._last_metadata["size_bytes"], elapsed_s)

            return {
                "success": True,
                "simulated": False,
                "image_path": str(target_path),
                "filename": target_path.name,
                "width": self._last_metadata["width"],
                "height": self._last_metadata["height"],
                "size_bytes": self._last_metadata["size_bytes"],
                "file_size_bytes": self._last_metadata["size_bytes"],
                "format": "JPEG",
                "timestamp": self._last_capture_time,
                "camera_model": self._camera_model,
                "backend": "camera_service_picamera2",
                "duration_s": elapsed_s,
                "message": f"Real photograph captured successfully and saved to {target_path}",
            }
        except Exception as exc:
            elapsed_s = round(time.perf_counter() - t0, 3)
            logger.error("Exception fetching snapshot from camera service: %s", exc)
            return {
                "success": False,
                "simulated": False,
                "error": f"Failed to acquire snapshot from camera service: {exc}",
                "image_path": None,
                "duration_s": elapsed_s,
            }

    def capture_photo(
        self,
        custom_path: Optional[str] = None,
        width: int = 1280,
        height: int = 720,
        timeout_ms: int = 500,
    ) -> Dict[str, Any]:
        """
        Capture a real photograph from the Sony IMX708 camera.
        Prefers the active camera vision service (avoiding pipeline busy locks),
        falling back to direct hardware rpicam-still only if the service is inactive.
        Saves image into /home/roshan/Pictures or custom_path.
        Returns validated capture metadata or raises/returns explicit error.
        """
        acquired = self._lock.acquire(timeout=10.0)
        if not acquired:
            return {
                "success": False,
                "simulated": False,
                "error": "Camera is busy with another capture process (lock acquisition timeout)",
                "image_path": None,
            }

        try:
            self._is_capturing = True
            now = datetime.datetime.now()
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")

            if custom_path:
                target_path = Path(custom_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                target_path = PICTURES_DIR / f"JARVIS_Photo_{timestamp_str}.jpg"

            # Ensure unique filename
            counter = 1
            stem = target_path.stem
            while target_path.exists():
                target_path = target_path.parent / f"{stem}_{counter}.jpg"
                counter += 1

            # 1. First priority: Use dedicated camera service if running (avoids pipeline handler conflicts)
            if self.is_service_running():
                return self._capture_from_service(target_path, width=width, height=height)

            # 2. Fallback: Direct rpicam-still capture if no service is running
            if not self._cli_binary:
                return {
                    "success": False,
                    "simulated": False,
                    "error": "Camera service offline and no camera binary found (rpicam-still not installed)",
                    "image_path": None,
                }

            cmd = [
                self._cli_binary,
                "-t", str(timeout_ms),
                "-o", str(target_path),
                "--width", str(width),
                "--height", str(height),
                "-n",  # no preview window
            ]

            t0 = time.perf_counter()
            logger.info("Executing real camera capture: %s", " ".join(cmd))
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12.0)
            elapsed_s = round(time.perf_counter() - t0, 3)

            if proc.returncode != 0:
                err = proc.stderr.strip() or f"rpicam return code {proc.returncode}"
                logger.error("Camera capture process failed: %s", err)
                return {
                    "success": False,
                    "error": f"Camera hardware capture failed: {err}",
                    "image_path": None,
                    "duration_s": elapsed_s,
                }

            # Thorough validation of the output file
            val_ok, val_err, img_info = self._validate_image_file(target_path)
            if not val_ok:
                logger.error("Captured image validation failed: %s", val_err)
                target_path.unlink(missing_ok=True)
                return {
                    "success": False,
                    "error": f"Captured image failed validation: {val_err}",
                    "image_path": None,
                }

            self._last_capture_time = time.time()
            self._last_image_path = str(target_path)
            self._last_metadata = {
                "filename": target_path.name,
                "path": str(target_path),
                "width": img_info.get("width", width),
                "height": img_info.get("height", height),
                "size_bytes": img_info.get("size_bytes", 0),
                "timestamp": self._last_capture_time,
                "camera_model": self._camera_model,
                "duration_s": elapsed_s,
            }

            logger.info("✓ Real camera capture verified: %s (%dx%d, %d bytes, %.2fs)",
                        target_path.name, self._last_metadata["width"],
                        self._last_metadata["height"], self._last_metadata["size_bytes"], elapsed_s)

            return {
                "success": True,
                "image_path": str(target_path),
                "filename": target_path.name,
                "width": self._last_metadata["width"],
                "height": self._last_metadata["height"],
                "size_bytes": self._last_metadata["size_bytes"],
                "file_size_bytes": self._last_metadata["size_bytes"],
                "format": "JPEG",
                "timestamp": self._last_capture_time,
                "camera_model": self._camera_model,
                "duration_s": elapsed_s,
                "message": f"Real photograph captured successfully and saved to {target_path}",
            }

        except subprocess.TimeoutExpired:
            logger.error("Camera capture process timed out (>12s).")
            return {
                "success": False,
                "error": "Camera capture process timed out (hardware unresponsive)",
                "image_path": None,
            }
        except Exception as exc:
            logger.error("Unexpected camera capture exception: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "image_path": None,
            }
        finally:
            self._is_capturing = False
            self._lock.release()

    def _validate_image_file(self, path: Path) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Verify image file exists, has content > 1KB, valid JPEG header, and valid dimensions."""
        if not path.exists():
            return False, "Output file was not created", {}
        size = path.stat().st_size
        if size < 1024:
            return False, f"Output file is too small ({size} bytes, expected > 1KB)", {}

        try:
            from PIL import Image
            with Image.open(path) as img:
                img.verify()
            # Reopen to check dimensions
            with Image.open(path) as img:
                w, h = img.size
                fmt = img.format
                if fmt != "JPEG":
                    return False, f"File format is {fmt}, expected JPEG", {}
                if w < 100 or h < 100:
                    return False, f"Invalid image dimensions: {w}x{h}", {}
                return True, None, {"width": w, "height": h, "size_bytes": size, "format": fmt}
        except Exception as e:
            return False, f"Image decoding error: {e}", {}


camera_manager = CameraManager()
