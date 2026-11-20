"""
Tests for permission-based gating of camera, vision and computer-interaction
hardware access.

Verifies that a GUEST session is denied access to vision/computer hardware
actions while a USER session is allowed.  All hardware is mocked so no physical
camera, display, or input device is required; tests assert against the stable
permission_manager interface and the REST API via TestClient.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.core.main import app
from tools.identity.permission_manager import permission_manager
from tools.identity.user_manager import UserRole

VISION_TOOLS = ("camera_capture", "camera_describe", "detect_objects", "identify_user")
COMPUTER_TOOLS = ("desktop_screenshot", "desktop_perception", "computer_click", "computer_type")


def _set_active_user(role: str) -> None:
    permission_manager.set_active_user(
        {
            "user_id": "perm_test_user",
            "display_name": "Permission Test User",
            "role": role,
        }
    )


def _clear_active_user() -> None:
    permission_manager._current_user = None


class TestPermissionManagerGating:
    """Unit-level checks against the stable permission_manager interface."""

    def setup_method(self):
        _clear_active_user()

    def teardown_method(self):
        _clear_active_user()

    def test_guest_denied_vision_tools(self):
        _set_active_user(UserRole.GUEST.value)
        for tool in VISION_TOOLS:
            allowed, reason = permission_manager.check_tool_permission(tool)
            assert allowed is False, f"GUEST must be denied {tool}: {reason}"
            assert "denied" in reason.lower() or "requires" in reason.lower()

    def test_user_allowed_vision_tools(self):
        _set_active_user(UserRole.USER.value)
        for tool in VISION_TOOLS:
            allowed, reason = permission_manager.check_tool_permission(tool)
            assert allowed is True, f"USER must be allowed {tool}: {reason}"

    def test_guest_denied_computer_tools(self):
        _set_active_user(UserRole.GUEST.value)
        for tool in COMPUTER_TOOLS:
            allowed, reason = permission_manager.check_tool_permission(tool)
            assert allowed is False, f"GUEST must be denied {tool}: {reason}"

    def test_user_allowed_computer_tools(self):
        _set_active_user(UserRole.USER.value)
        for tool in COMPUTER_TOOLS:
            allowed, reason = permission_manager.check_tool_permission(tool)
            assert allowed is True, f"USER must be allowed {tool}: {reason}"

    def test_admin_wildcard_allows_all(self):
        _set_active_user(UserRole.ADMIN.value)
        for tool in VISION_TOOLS + COMPUTER_TOOLS:
            allowed, _ = permission_manager.check_tool_permission(tool)
            assert allowed is True, f"ADMIN wildcard must allow {tool}"


class TestVisionApiPermissionGating:
    """API-level checks with the vision service mocked (no camera hardware)."""

    def setup_method(self):
        _clear_active_user()

    def teardown_method(self):
        _clear_active_user()

    @patch("apps.api.vision_api.vision_service.capture_frame")
    @patch("apps.api.vision_api.vision_service.detect_objects")
    @patch("apps.api.vision_api.vision_service.describe_scene")
    def test_capture_detect_describe_guest_denied_user_allowed(
        self, mock_describe, mock_detect, mock_capture
    ):
        client = TestClient(app)
        mock_capture.return_value = {"status": "ok", "simulated": True, "image_path": None}
        mock_detect.return_value = {
            "status": "ok",
            "success": True,
            "objects": [],
            "labels": [],
            "inference_ms": 1.0,
        }
        mock_describe.return_value = "A simulated scene."

        # GUEST: hardware access denied with 403; vision service never invoked
        _set_active_user(UserRole.GUEST.value)
        assert client.post("/api/vision/capture").status_code == 403
        assert client.post("/api/vision/detect", json={}).status_code == 403
        assert client.get("/api/vision/describe").status_code == 403
        mock_capture.assert_not_called()
        mock_detect.assert_not_called()
        mock_describe.assert_not_called()

        # USER: hardware access allowed; mocked service invoked
        _set_active_user(UserRole.USER.value)
        assert client.post("/api/vision/capture").status_code == 200
        assert client.post("/api/vision/detect", json={}).status_code == 200
        assert client.get("/api/vision/describe").status_code == 200

    @patch("apps.api.vision_api.vision_service.camera_status")
    def test_status_endpoint_ungated_for_guest(self, mock_status):
        """Read-only telemetry remains available to every role."""
        mock_status.return_value = {
            "available": False,
            "simulation": True,
            "backend": "simulated",
            "yolo_ready": True,
            "vlm_ready": False,
        }
        client = TestClient(app)
        _set_active_user(UserRole.GUEST.value)
        assert client.get("/api/vision/status").status_code == 200


class TestComputerApiPermissionGating:
    """API-level checks with the desktop perception mocked (no display hardware)."""

    def setup_method(self):
        _clear_active_user()

    def teardown_method(self):
        _clear_active_user()

    @patch("apps.api.computer_api.desktop_perception.capture_fullscreen")
    def test_screenshot_guest_denied_user_allowed(self, mock_capture):
        client = TestClient(app)
        mock_capture.return_value = {
            "status": "ok",
            "width": 640,
            "height": 480,
            "size_bytes": 1234,
            "hash": "abcd",
        }

        # GUEST denied
        _set_active_user(UserRole.GUEST.value)
        assert client.post("/api/computer/screenshot", json={}).status_code == 403
        mock_capture.assert_not_called()

        # USER allowed
        _set_active_user(UserRole.USER.value)
        assert client.post("/api/computer/screenshot", json={}).status_code == 200
        mock_capture.assert_called_once()

    @patch("apps.api.computer_api.desktop_perception.observe_desktop")
    def test_observe_guest_denied_user_allowed(self, mock_observe):
        client = TestClient(app)
        mock_observe.return_value = {"status": "ok", "timestamp": 1.0}

        _set_active_user(UserRole.GUEST.value)
        assert client.post("/api/computer/observe").status_code == 403

        _set_active_user(UserRole.USER.value)
        assert client.post("/api/computer/observe").status_code == 200

    def test_action_guest_denied_user_allowed(self):
        """Synthetic input actions are gated; unknown actions still 400."""
        client = TestClient(app)

        # GUEST: click denied before reaching the action engine
        _set_active_user(UserRole.GUEST.value)
        assert client.post(
            "/api/computer/action", json={"action": "click", "x": 10, "y": 10}
        ).status_code == 403

        # USER: known action allowed (passes permission; we only assert not 403
        # since the action engine may run without a real display)
        _set_active_user(UserRole.USER.value)
        res = client.post(
            "/api/computer/action", json={"action": "click", "x": 10, "y": 10}
        )
        assert res.status_code != 403

        # Unknown action is a 400 regardless of role
        _set_active_user(UserRole.USER.value)
        assert client.post(
            "/api/computer/action", json={"action": "not_a_real_action"}
        ).status_code == 400