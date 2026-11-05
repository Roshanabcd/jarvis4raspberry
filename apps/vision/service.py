"""
JARVIS Vision Service
Integrates Raspberry Pi Camera Module 3.
Supports:
1. Native libcamera / rpicam CLI (rpicam-still / rpicam-jpeg) - optimal on Raspberry Pi 5 under Debian Trixie.
2. picamera2 when available.
3. Simulation mode fallback when hardware is disconnected or simulation is enabled.
"""
import io
import os
import shutil
import logging
import subprocess
import tempfile
import time
import base64
from typing import Optional, Dict, Any
from config.config_manager import config

logger = logging.getLogger("JARVIS.Vision")

try:
    from picamera2 import Picamera2
    _PICAMERA_AVAILABLE = True
except ImportError:
    _PICAMERA_AVAILABLE = False


def _check_rpicam_available() -> bool:
    """Check if native rpicam-still or rpicam-jpeg binary exists."""
    return bool(shutil.which("rpicam-still") or shutil.which("rpicam-jpeg") or shutil.which("libcamera-still"))


class VisionService:
    """
    Camera integration for JARVIS on Raspberry Pi 5.

    Capture modes:
    - picamera2 (direct Python bindings)
    - rpicam-still (native ARM64 binary subprocess)
    - simulation (synthetic test frame and object list)
    """

    def __init__(self, width: int = 1280, height: int = 720,
                 simulation: Optional[bool] = None) -> None:
        self.width = width
        self.height = height

        cfg_sim = bool(config.get("simulation_mode", True))
        if simulation is not None:
            self.simulation = simulation
        else:
            self.simulation = cfg_sim

        self._camera: Optional[Any] = None
        self._last_capture: Optional[float] = None
        self._backend: str = "simulated"

        if not self.simulation:
            self._init_camera()
        else:
            logger.info("VisionService running in SIMULATION mode.")

    def _init_camera(self) -> None:
        """Probe and initialize camera hardware using available backends."""
        # 1. Try picamera2 if installed
        if _PICAMERA_AVAILABLE:
            try:
                self._camera = Picamera2()
                cfg = self._camera.create_still_configuration(
                    main={"size": (self.width, self.height), "format": "RGB888"}
                )
                self._camera.configure(cfg)
                self._camera.start()
                time.sleep(1)  # Sensor warmup
                self._backend = "picamera2"
                logger.info(f"Camera initialized via picamera2 at {self.width}x{self.height}")
                return
            except Exception as e:
                logger.warning(f"picamera2 initialization failed: {e}. Checking rpicam CLI...")
                self._camera = None

        # 2. Try native rpicam CLI (works on Pi 5 / Debian 13)
        rpicam_bin = shutil.which("rpicam-still") or shutil.which("rpicam-jpeg") or shutil.which("libcamera-still")
        if rpicam_bin:
            self._backend = "rpicam_cli"
            logger.info(f"Camera initialized via native binary: {rpicam_bin}")
            return

        # 3. Fallback to simulation
        logger.warning("No functional camera interface found. Falling back to simulation.")
        self.simulation = True
        self._backend = "simulated"

    def capture_frame(self) -> Dict[str, Any]:
        """
        Capture a single frame.
        Returns: {status, timestamp, width, height, format, data_b64, backend}
        """
        self._last_capture = time.time()

        if self.simulation or self._backend == "simulated":
            return {
                "status": "simulated",
                "timestamp": self._last_capture,
                "width": self.width,
                "height": self.height,
                "format": "simulated",
                "data_b64": None,
                "backend": "simulated",
                "objects_detected": ["desk", "monitor", "keyboard"],
                "description": "Simulated scene: office environment with robotics workbench.",
            }

        # 1. Capture via picamera2
        if self._backend == "picamera2" and self._camera:
            try:
                buf = io.BytesIO()
                self._camera.capture_file(buf, format="jpeg")
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode("utf-8")
                return {
                    "status": "ok",
                    "timestamp": self._last_capture,
                    "width": self.width,
                    "height": self.height,
                    "format": "jpeg",
                    "data_b64": b64,
                    "backend": "picamera2",
                }
            except Exception as e:
                logger.error(f"picamera2 capture failed: {e}")
                return {"status": "error", "error": str(e), "timestamp": time.time(), "backend": "picamera2"}

        # 2. Capture via native rpicam-still binary
        if self._backend == "rpicam_cli":
            rpicam_bin = shutil.which("rpicam-still") or shutil.which("rpicam-jpeg") or shutil.which("libcamera-still")
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                cmd = [
                    rpicam_bin,
                    "-t", "500",
                    "-o", tmp_path,
                    "--width", str(self.width),
                    "--height", str(self.height),
                    "-n",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                if res.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    with open(tmp_path, "rb") as f:
                        img_bytes = f.read()
                    b64 = base64.b64encode(img_bytes).decode("utf-8")
                    return {
                        "status": "ok",
                        "timestamp": self._last_capture,
                        "width": self.width,
                        "height": self.height,
                        "format": "jpeg",
                        "size_bytes": len(img_bytes),
                        "data_b64": b64,
                        "backend": "rpicam_cli",
                    }
                else:
                    err_msg = res.stderr.strip() or f"rpicam return code {res.returncode}"
                    logger.warning(f"rpicam capture command failed: {err_msg}")
                    return {"status": "error", "error": err_msg, "timestamp": time.time(), "backend": "rpicam_cli"}
            except subprocess.TimeoutExpired:
                logger.error("rpicam-still capture timed out.")
                return {"status": "timeout", "error": "Camera capture timed out", "backend": "rpicam_cli"}
            except Exception as exc:
                logger.error(f"rpicam capture error: {exc}")
                return {"status": "error", "error": str(exc), "backend": "rpicam_cli"}
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

        return {"status": "error", "error": "Unknown camera backend", "backend": self._backend}

    def detect_objects(self) -> Dict[str, Any]:
        """Detect objects in captured frame."""
        frame = self.capture_frame()
        if frame.get("status") == "simulated":
            return {
                "objects": frame.get("objects_detected", []),
                "source": "simulation",
            }
        return {
            "objects": [],
            "source": self._backend,
            "note": "Vision detection pipeline ready. Frame captured successfully.",
            "status": frame.get("status"),
        }

    def describe_scene(self) -> str:
        """Describe current camera scene."""
        frame = self.capture_frame()
        if frame.get("status") == "simulated":
            return frame.get("description", "Simulated scene.")
        if frame.get("status") == "ok":
            return f"Hardware frame captured via {self._backend} ({self.width}x{self.height}). Ready for vision model inference."
        return f"Camera capture unavailable: {frame.get('error', 'unknown error')}"

    def camera_status(self) -> dict:
        return {
            "available": not self.simulation and self._backend != "simulated",
            "simulation": self.simulation,
            "backend": self._backend,
            "picamera2_installed": _PICAMERA_AVAILABLE,
            "rpicam_cli_available": _check_rpicam_available(),
            "last_capture": self._last_capture,
            "resolution": f"{self.width}x{self.height}",
        }

    def shutdown(self) -> None:
        if self._camera:
            try:
                self._camera.stop()
                self._camera.close()
                logger.info("Camera closed.")
            except Exception as e:
                logger.warning(f"Camera shutdown error: {e}")
        self._backend = "simulated"
