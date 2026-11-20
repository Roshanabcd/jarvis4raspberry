"""Focused hardware-safe regression tests for the security hardening milestone.

These tests deliberately build small FastAPI applications around individual
routers.  They never import ``apps.core.main``, start its lifespan, create a
camera/microphone owner, or open I2C/serial hardware.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

from apps.api import admin_action_policy, apps_center_api, robot_api, settings_api
from apps.apps_center.permissions import AppRequestIdentity
import tools.robotics.controller as robot_controller_module
from apps.voice import remote_control_policy
from tools.robotics.controller import RobotController


class FakeAppsDatabase:
    """Small in-memory stand-in that records the server-resolved owner."""

    def __init__(self) -> None:
        self.favorites: dict[str, set[str]] = {}
        self.settings: dict[tuple[str, str, str], object] = {}
        self.opened: list[tuple[str, str]] = []

    def get_user_favorites(self, user_id: str):
        return sorted(self.favorites.get(user_id, set()))

    def toggle_favorite(self, user_id: str, app_id: str) -> bool:
        favorites = self.favorites.setdefault(user_id, set())
        if app_id in favorites:
            favorites.remove(app_id)
            return False
        favorites.add(app_id)
        return True

    def record_app_opened(self, user_id: str, app_id: str) -> None:
        self.opened.append((user_id, app_id))

    def get_recently_opened(self, user_id: str, limit: int = 6):
        return [
            {"app_id": app_id, "opened_at": "2026-01-01T00:00:00Z"}
            for owner, app_id in self.opened
            if owner == user_id
        ][-limit:]

    def get_app_settings(self, app_id: str, user_id: str):
        return {
            key: value
            for (owner, stored_app_id, key), value in self.settings.items()
            if owner == user_id and stored_app_id == app_id
        }

    def set_app_setting(self, app_id: str, user_id: str, key: str, value: object) -> None:
        self.settings[(user_id, app_id, key)] = value


def _apps_client(identity: AppRequestIdentity, db: FakeAppsDatabase) -> TestClient:
    app = FastAPI()
    app.include_router(apps_center_api.apps_center_router, prefix="/api")
    app.dependency_overrides[apps_center_api.get_active_app_identity] = lambda: identity
    return TestClient(app)


def test_apps_center_rejects_client_owned_identity_fields(monkeypatch: pytest.MonkeyPatch):
    """A browser cannot claim a different user ID or role through Apps Center."""
    fake_db = FakeAppsDatabase()
    monkeypatch.setattr(apps_center_api, "apps_db", fake_db)
    identity = AppRequestIdentity("verified_user", "Verified User", "USER")

    with _apps_client(identity, fake_db) as client:
        # Request bodies containing the retired identity field are invalid.
        spoofed_launch = client.post("/api/apps/launch/voice-assistant", json={"user_id": "attacker"})
        assert spoofed_launch.status_code == 422

        # Query parameters are ignored rather than used as ownership evidence.
        favorite = client.post("/api/apps/favorite/voice-assistant?user_id=attacker")
        assert favorite.status_code == 200
        assert "voice-assistant" in fake_db.favorites["verified_user"]
        assert "attacker" not in fake_db.favorites

        launched = client.post("/api/apps/launch/voice-assistant", json={})
        assert launched.status_code == 200
        assert fake_db.opened == [("verified_user", "voice-assistant")]

        spoofed_settings = client.post(
            "/api/apps/settings/voice-assistant",
            json={"user_id": "attacker", "settings": {"speech_speed": 1.1}},
        )
        assert spoofed_settings.status_code == 422

        saved = client.post(
            "/api/apps/settings/voice-assistant",
            json={"settings": {"speech_speed": 1.1}},
        )
        assert saved.status_code == 200
        assert fake_db.get_app_settings("voice-assistant", "verified_user") == {"speech_speed": 1.1}


def test_apps_center_guest_cannot_launch_user_application(monkeypatch: pytest.MonkeyPatch):
    fake_db = FakeAppsDatabase()
    monkeypatch.setattr(apps_center_api, "apps_db", fake_db)

    with _apps_client(AppRequestIdentity("guest_session", "Guest", "GUEST"), fake_db) as client:
        response = client.post("/api/apps/launch/voice-assistant", json={})

    assert response.status_code == 403
    assert "requires USER role" in response.json()["detail"]
    assert fake_db.opened == []


class RecordingServo:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int, int]] = []

    def set_pwm(self, channel: int, on: int, off: int) -> bool:
        self.calls.append((channel, on, off))
        return True


class RecordingMotor:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def send_command(self, command: str) -> bool:
        self.commands.append(command)
        return True


def test_servo_never_bypasses_disarm_or_emergency_stop():
    servo = RecordingServo()
    motor = RecordingMotor()
    controller = RobotController(servo_controller=servo, motor_controller=motor)
    controller.simulated = False  # Exercise the fake PWM interface, never hardware.

    assert controller.set_servo(0, 90) is False
    assert servo.calls == []

    controller.arm()
    assert controller.set_servo(0, 90) is True
    assert servo.calls == [(0, 0, 375)]

    controller.emergency_stop()
    assert controller.set_servo(0, 45) is False
    assert servo.calls == [(0, 0, 375)]


def test_get_existing_robot_does_not_construct_a_controller(monkeypatch: pytest.MonkeyPatch):
    """Lifecycle code can inspect ownership without opening I2C or serial."""
    monkeypatch.setattr(robot_controller_module, "_robot", None)

    assert robot_controller_module.get_existing_robot() is None


def test_disabled_http_actuation_does_not_resolve_a_robot(monkeypatch: pytest.MonkeyPatch):
    """The default HTTP policy fails before a controller can be constructed."""
    app = FastAPI()
    app.include_router(robot_api.robot_router, prefix="/api")
    resolved = False

    def unexpected_robot():
        nonlocal resolved
        resolved = True
        raise AssertionError("disabled actuation must not resolve a robot")

    monkeypatch.setattr(robot_api, "get_robot", unexpected_robot)
    monkeypatch.setattr(robot_api, "_http_actuation_enabled", lambda: False)

    with TestClient(app) as client:
        response = client.post("/api/robot/forward?speed=20")

    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()
    assert resolved is False


def test_external_voice_control_is_off_before_any_pin_or_network_action(monkeypatch: pytest.MonkeyPatch):
    """Remote-provider controls are opt-in and fail before PIN verification."""
    pin_checked = False

    def unexpected_pin_check(_: str):
        nonlocal pin_checked
        pin_checked = True
        raise AssertionError("disabled remote control must not check a PIN")

    monkeypatch.setattr(remote_control_policy, "_manual_remote_voice_control_enabled", lambda: False)
    monkeypatch.setattr(remote_control_policy.user_manager, "verify_admin_pin", unexpected_pin_check)

    with pytest.raises(HTTPException) as error:
        remote_control_policy.require_external_voice_control(
            x_jarvis_admin_pin="not-used",
            x_jarvis_external_voice_confirmation="external-voice-provider",
        )

    assert error.value.status_code == 403
    assert pin_checked is False


def test_settings_write_is_denied_before_config_or_env_mutation(monkeypatch: pytest.MonkeyPatch):
    """A local caller cannot enable remote features through the settings API."""
    writes: list[str] = []

    def unexpected_write(*args, **kwargs):
        writes.append("write")
        raise AssertionError("authorization must run before configuration persistence")

    monkeypatch.setattr(settings_api.config, "set", unexpected_write)
    monkeypatch.setattr(settings_api.config, "save", unexpected_write)
    monkeypatch.setattr(settings_api.config, "save_env", unexpected_write)

    app = FastAPI()
    app.include_router(settings_api.settings_router, prefix="/api")
    with TestClient(app) as client:
        response = client.post(
            "/api/settings/voice",
            json={
                "settings": {"remote_voice_enabled": True},
                "env_updates": {"OMNIVOICE_REGISTRATION_TOKEN": "attacker-value"},
            },
        )

    assert response.status_code == 428
    assert writes == []


def test_settings_backup_and_diagnostics_require_confirmation():
    """Sensitive settings routes deny requests before dispatching their bodies."""
    app = FastAPI()
    app.include_router(settings_api.settings_router, prefix="/api")

    with TestClient(app) as client:
        backup = client.get("/api/settings/export/backup")
        microphone = client.post("/api/settings/test/microphone")

    assert backup.status_code == 428
    assert microphone.status_code == 428


def test_settings_write_accepts_a_fresh_confirmed_admin_pin(monkeypatch: pytest.MonkeyPatch):
    """The dashboard's two headers reach the privileged settings dependency."""
    writes: list[tuple[str, object]] = []

    monkeypatch.setattr(
        admin_action_policy.user_manager,
        "verify_admin_pin",
        lambda pin: (pin == "test-pin", "ok"),
    )
    monkeypatch.setattr(settings_api.config, "set", lambda key, value: writes.append((key, value)))
    monkeypatch.setattr(settings_api.config, "save", lambda: True)

    app = FastAPI()
    app.include_router(settings_api.settings_router, prefix="/api")
    with TestClient(app) as client:
        response = client.post(
            "/api/settings/voice",
            headers={
                "X-Jarvis-Admin-Pin": "test-pin",
                "X-Jarvis-Admin-Confirmation": "privileged-settings-action",
            },
            json={"voice": {"remote_voice_enabled": False}},
        )

    assert response.status_code == 200
    assert any(key == "voice" for key, _ in writes)


def test_settings_robot_status_never_constructs_a_controller(monkeypatch: pytest.MonkeyPatch):
    """Settings rendering describes an unowned controller without opening I2C/serial."""
    monkeypatch.setattr(settings_api, "get_existing_robot", lambda: None)

    status = settings_api._robot_status()

    assert status["controller_initialized"] is False
    assert status["armed"] is False


def test_colab_runner_endpoint_is_disabled_before_runner_import(monkeypatch: pytest.MonkeyPatch):
    """The HTTP endpoint cannot start a remote workload under default config."""
    from apps.api.voice_api import voice_router

    app = FastAPI()
    app.include_router(voice_router, prefix="/api")
    monkeypatch.setattr(remote_control_policy, "_manual_remote_voice_control_enabled", lambda: False)

    with TestClient(app) as client:
        response = client.post("/api/voice/colab/runner/start")

    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


class SilentFallbackTTS:
    """A local stand-in that proves a unit test never plays real audio."""

    backend = "silent-test-fallback"

    def __init__(self) -> None:
        self.spoken: list[str] = []

    def speak_sync(self, text: str) -> None:
        self.spoken.append(text)


def test_remote_voice_is_disabled_before_any_network_probe(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """A configured remote URL must not turn status or fallback speech into I/O."""
    import requests
    from apps.voice.gradio_tts import GradioVoiceCloner

    outbound_calls: list[tuple[str, str]] = []

    def unexpected_request(method: str):
        def _request(url, *args, **kwargs):
            outbound_calls.append((method, str(url)))
            raise AssertionError("remote voice is disabled; no HTTP request is allowed")
        return _request

    monkeypatch.setattr(requests, "head", unexpected_request("HEAD"))
    monkeypatch.setattr(requests, "get", unexpected_request("GET"))

    fallback = SilentFallbackTTS()
    default_cloner = GradioVoiceCloner(
        cache_dir=str(tmp_path / "default-voice-cache"),
        fallback_tts=fallback,
        remote_voice_enabled=False,
        cloud_tts_enabled=False,
    )
    # config.yaml contains a legacy Gradio URL, but a disabled default cloner
    # must not bind it as an outbound destination.
    assert default_cloner.gradio_url == ""

    cloner = GradioVoiceCloner(
        gradio_url="https://example.invalid/voice",
        cache_dir=str(tmp_path / "voice-cache"),
        fallback_tts=fallback,
        remote_voice_enabled=False,
        cloud_tts_enabled=False,
    )

    status = cloner.get_provider_status()
    assert status["online"] is False
    assert status["remote_voice_enabled"] is False

    # A local fallback is permitted, but neither a Gradio probe nor cloud TTS
    # may run when both remote features are disabled.
    result = cloner.synthesize("Safety regression test")
    assert result.success is True
    assert result.provider in {"espeak_local_tts", "fallback_local_tts"}
    assert outbound_calls == []
