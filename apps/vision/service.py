"""
JARVIS Vision Service
Integrates Raspberry Pi Camera Module 3.
Uses picamera2 when available. Gracefully degrades in simulation.
"""
import io
import logging
import time
import base64
from typing import Optional, Dict, Any

logger = logging.getLogger("JARVIS.Vision")

try:
    from picamera2 import Picamera2
    _PICAMERA_AVAILABLE = True
except ImportError:
    _PICAMERA_AVAILABLE = False
    logger.warning("picamera2 not available — vision running in simulation mode.")


class VisionService:
    """
    Camera integration for JARVIS.

    Default config:
    - Resolution: 1280x720
    - Format: JPEG
    - Frame capture on-demand (not continuous stream to save CPU)
    - Vision AI analysis is triggered explicitly, not on every frame.
    """

    def __init__(self, width: int = 1280, height: int = 720,
                 simulation: bool = True) -> None:
        self.width = width
        self.height = height
        self.simulation = simulation or not _PICAMERA_AVAILABLE
        self._camera: Optional[Any] = None
        self._last_capture: Optional[float] = None

        if not self.simulation:
            self._init_camera()
        else:
            logger.info("VisionService running in SIMULATION mode.")

    def _init_camera(self) -> None:
        try:
            self._camera = Picamera2()
            cfg = self._camera.create_still_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            self._camera.configure(cfg)
            self._camera.start()
            time.sleep(2)  # warm-up
            logger.info(f"Camera initialized at {self.width}x{self.height}")
        except Exception as e:
            logger.error(f"Camera init failed: {e}. Falling back to simulation.")
            self.simulation = True
            self._camera = None

    def capture_frame(self) -> Dict[str, Any]:
        """
        Capture a single frame.
        Returns: {status, timestamp, width, height, format, data_b64}
        data_b64 is base64-encoded JPEG in real mode, None in simulation.
        """
        self._last_capture = time.time()

        if self.simulation:
            return {
                "status": "simulated",
                "timestamp": self._last_capture,
                "width": self.width,
                "height": self.height,
                "format": "simulated",
                "data_b64": None,
                "objects_detected": ["desk", "monitor", "keyboard"],
                "description": "Simulated scene: office environment.",
            }

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
            }
        except Exception as e:
            logger.error(f"Frame capture failed: {e}")
            return {"status": "error", "error": str(e), "timestamp": time.time()}

    def detect_objects(self) -> Dict[str, Any]:
        """
        Placeholder for object detection pipeline.
        In production: pass frame to vision model (e.g., YOLO / OpenAI Vision).
        """
        frame = self.capture_frame()
        if frame["status"] == "simulated":
            return {"objects": frame.get("objects_detected", []),
                    "source": "simulation"}
        # TODO: integrate YOLO or cloud vision model
        return {"objects": [], "source": "real_camera", "note": "Detection model not yet configured."}

    def describe_scene(self) -> str:
        """Ask AI to describe the current scene (placeholder for AI vision call)."""
        frame = self.capture_frame()
        if frame["status"] == "simulated":
            return frame.get("description", "Simulated scene.")
        return "Scene description requires a configured vision AI model."

    def camera_status(self) -> dict:
        return {
            "available": not self.simulation,
            "simulation": self.simulation,
            "picamera2_installed": _PICAMERA_AVAILABLE,
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
