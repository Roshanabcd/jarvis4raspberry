"""Phase 9 regression tests for trusted voice identity and authorization."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from apps.api.voice_api import CommandRequest, run_command
from apps.voice.stt import SpeechToText
from apps.voice.session_manager import voice_session_mgr


@pytest.fixture(autouse=True)
def reset_voice_session():
    """Keep singleton session state from leaking between security tests."""
    voice_session_mgr.invalidate_session()
    yield
    voice_session_mgr.invalidate_session()


def test_admin_face_match_needs_pin_before_admin_authorization():
    session = voice_session_mgr.create_session(
        user_id="admin_test",
        display_name="Administrator",
        role="ADMIN",
        source="face_biometrics",
    )

    assert session.role == "ADMIN"
    assert session.is_admin_elevated is False
    assert session.authorization_role() == "USER"


def test_successful_pin_elevates_only_the_active_voice_session():
    voice_session_mgr.create_session(
        user_id="admin_test",
        display_name="Administrator",
        role="ADMIN",
        source="face_biometrics",
    )

    with patch("apps.voice.session_manager.user_manager.verify_admin_pin", return_value=(True, "verified")), patch(
        "apps.voice.session_manager.user_manager.get_admin_user",
        return_value={"user_id": "admin_test", "display_name": "Administrator"},
    ):
        verified, _ = voice_session_mgr.verify_admin_pin("1234")

    assert verified is True
    assert voice_session_mgr.get_active_session().authorization_role() == "ADMIN"


def test_camera_identification_uses_service_capture_result_and_image_path():
    capture = {"success": True, "image_path": "/tmp/camera-service-frame.jpg"}
    identity = {
        "identified": True,
        "user_id": "user_123",
        "display_name": "Roshan",
        "role": "USER",
        "confidence": 0.91,
    }
    with patch("apps.voice.session_manager.camera_manager.capture_photo", return_value=capture) as capture_photo, patch(
        "apps.voice.session_manager.user_manager.identify_user_from_image", return_value=identity
    ) as identify:
        result = voice_session_mgr.identify_speaker_from_camera()

    capture_photo.assert_called_once_with()
    identify.assert_called_once_with("/tmp/camera-service-frame.jpg")
    assert result["success"] is True
    assert result["identified"] is True
    assert result["authorization_role"] == "USER"


def test_camera_failure_keeps_a_safe_guest_session():
    with patch(
        "apps.voice.session_manager.camera_manager.capture_photo",
        return_value={"success": False, "error": "camera service offline"},
    ):
        result = voice_session_mgr.identify_speaker_from_camera()

    assert result["success"] is False
    assert result["session"]["role"] == "GUEST"


def test_voice_command_rejects_caller_supplied_identity_fields():
    with pytest.raises(ValidationError):
        CommandRequest(text="open terminal", user_id="attacker", role="ADMIN")


def test_voice_command_uses_server_owned_session():
    voice_session_mgr.create_session(
        user_id="user_123",
        display_name="Roshan",
        role="USER",
        source="face_biometrics",
    )

    with patch("apps.api.voice_api.voice_service.process_command", return_value="Done.") as process, patch(
        "apps.api.voice_api.voice_service.enqueue_response"
    ) as enqueue:
        response = run_command(CommandRequest(text="check status"))

    assert response["response"] == "Done."
    process.assert_called_once_with("check status", speak=False)
    enqueue.assert_called_once_with("Done.", broadcast=False)


def test_whisper_loading_is_deferred_until_a_real_transcription_needs_it():
    stt = SpeechToText(simulation_mode=False)

    assert stt.model is None
    assert stt._model_load_attempted is False

