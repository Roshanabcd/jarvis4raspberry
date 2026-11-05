"""
Tests for Vision Service and Raspberry Pi Camera Module 3 Support.
"""

import pytest
from apps.vision.service import VisionService, _check_rpicam_available


class TestVisionService:
    def test_simulation_capture(self):
        vs = VisionService(width=640, height=480, simulation=True)
        frame = vs.capture_frame()
        assert frame["status"] == "simulated"
        assert frame["backend"] == "simulated"
        assert frame["width"] == 640
        assert frame["height"] == 480
        assert len(frame.get("objects_detected", [])) > 0

    def test_camera_status(self):
        vs = VisionService(width=640, height=480, simulation=True)
        status = vs.camera_status()
        assert "available" in status
        assert "simulation" in status
        assert "backend" in status
        assert status["resolution"] == "640x480"

    def test_describe_scene_simulation(self):
        vs = VisionService(simulation=True)
        desc = vs.describe_scene()
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_detect_objects_simulation(self):
        vs = VisionService(simulation=True)
        objs = vs.detect_objects()
        assert objs["source"] == "simulation"
        assert len(objs["objects"]) > 0

    def test_shutdown_simulation(self):
        vs = VisionService(simulation=True)
        vs.shutdown()
        assert vs._backend == "simulated"

    def test_hardware_rpicam_capture_if_available(self):
        """If rpicam-still is present on this Pi 5, test real hardware capture."""
        if not _check_rpicam_available():
            pytest.skip("rpicam binary not found on this system")

        vs = VisionService(width=640, height=480, simulation=False)
        if vs.simulation or vs._backend == "simulated":
            pytest.skip("Physical camera not detected by backend")

        frame = vs.capture_frame()
        assert frame["status"] == "ok"
        assert frame["backend"] in ("rpicam_cli", "picamera2")
        assert frame["data_b64"] is not None
        assert frame.get("size_bytes", 0) > 1000
