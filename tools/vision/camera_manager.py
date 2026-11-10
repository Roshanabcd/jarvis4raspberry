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
import logging
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("JARVIS.Vision.CameraManager")

PICTURES_DIR = Path("/home/roshan/Pictures")
PICTURES_DIR.mkdir(parents=True, exist_ok=True)


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

    def is_camera_available(self) -> bool:
        """Verify camera binary exists and Sony IMX708 is connected."""
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
        """Return truthful hardware status dictionary."""
        available = self.is_camera_available()
        return {
            "available": available,
            "camera_model": self._camera_model,
            "binary": self._cli_binary,
            "is_capturing": self._is_capturing,
            "last_capture_time": self._last_capture_time,
            "last_image_path": self._last_image_path,
            "last_metadata": self._last_metadata,
            "save_directory": str(PICTURES_DIR),
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
        Saves image into /home/roshan/Pictures or custom_path.
        Returns validated capture metadata or raises/returns explicit error.
        """
        if not self._cli_binary:
            return {
                "success": False,
                "error": "No camera binary found (rpicam-still/libcamera-still not installed)",
                "image_path": None,
            }

        acquired = self._lock.acquire(timeout=10.0)
        if not acquired:
            return {
                "success": False,
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
