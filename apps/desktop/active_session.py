"""Single, leased desktop session. Frames stay in RAM and expire on disconnect."""
from __future__ import annotations

import io
import secrets
import threading
import time
from typing import Callable

from PIL import Image


class VoiceLease:
    """Borrow the existing voice owner; restore only state changed by this lease."""
    def __init__(self):
        self.owned = False
        self.restore_mute = False
        self.service = None

    def start(self):
        from apps.voice.wake_word_engine import is_voice_service_daemon_running, wake_word_engine
        if is_voice_service_daemon_running():
            return {"state": "external_owner", "detail": "Existing voice daemon owns the microphone; no second capture started."}
        from apps.voice.service import voice_service
        self.service = voice_service
        self.restore_mute = voice_service.is_muted()
        self.owned = not wake_word_engine._is_running
        if self.owned:
            voice_service.start()
        if self.restore_mute:
            voice_service.unmute()
        state = voice_service.get_state()
        return {"state": "listening" if state.get("listening") and state.get("microphone_available") else "unavailable",
                "detail": state.get("state", "unknown")}

    def stop(self):
        if self.service is not None:
            if self.owned:
                self.service.stop()
            if self.restore_mute:
                self.service.mute()
        self.owned = self.restore_mute = False
        self.service = None


class ActiveDesktopSession:
    TTL = 30
    FRAME_TTL = 15
    MAX_BYTES = 2_000_000

    def __init__(self, voice_factory=VoiceLease, clock: Callable = time.monotonic):
        self._lock = threading.RLock()
        self._voice_factory = voice_factory
        self._clock = clock
        self._token = None
        self._voice = None
        self._frame = None
        self._frame_time = 0.0
        self._expires = 0.0
        self._options = {}
        self._microphone = {"state": "off"}
        self._watchdog = None

    def start(self, *, microphone=True, speaker=True, screen=True):
        with self._lock:
            self.expire()
            if self._token:
                raise RuntimeError("JARVIS is already active in another tab. Stop it there or wait for its lease to expire.")
            self._token = secrets.token_urlsafe(32)
            self._expires = self._clock() + self.TTL
            self._options = {"microphone": microphone, "speaker": speaker, "screen": screen}
            if microphone:
                self._voice = self._voice_factory()
                try:
                    self._microphone = self._voice.start()
                except Exception:
                    self._microphone = {"state": "unavailable", "detail": "Voice startup failed"}
            if self._watchdog is None or not self._watchdog.is_alive():
                self._watchdog = threading.Thread(target=self._watch, daemon=True, name="DesktopLease")
                self._watchdog.start()
            return {"token": self._token, **self.status()}

    def _watch(self):
        while True:
            time.sleep(2)
            with self._lock:
                self.expire()

    def _check(self, token):
        self.expire()
        if not self._token or not isinstance(token, str) or not secrets.compare_digest(self._token, token):
            raise PermissionError("Inactive or invalid desktop session")

    def heartbeat(self, token):
        with self._lock:
            self._check(token)
            self._expires = self._clock() + self.TTL
            return self.status()

    def expire(self):
        with self._lock:
            if self._token and self._clock() >= self._expires:
                self._stop()

    def _stop(self):
        self._token = None
        self._frame = None
        self._frame_time = 0.0
        self._options = {}
        self._microphone = {"state": "off"}
        if self._voice:
            try:
                self._voice.stop()
            finally:
                self._voice = None

    def stop(self, token):
        with self._lock:
            self._check(token)
            self._stop()
            return self.status()

    def status(self):
        with self._lock:
            self.expire()
            age = self._clock() - self._frame_time if self._frame is not None else None
            if age is not None and age > self.FRAME_TTL:
                self._frame = None
            return {"active": bool(self._token), "options": dict(self._options),
                    "microphone": dict(self._microphone),
                    "screen": "receiving" if self._frame else "waiting" if self._options.get("screen") else "off",
                    "frame_age_seconds": round(age, 1) if age is not None else None,
                    "lease_seconds": self.TTL}

    def frame(self, token, data: bytes):
        with self._lock:
            self._check(token)
            if not self._options.get("screen"):
                raise ValueError("Screen sharing is disabled")
        if not data or len(data) > self.MAX_BYTES:
            raise ValueError("Frame must be between 1 byte and 2 MB")
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {"JPEG", "PNG"} or image.width * image.height > 4_000_000:
                raise ValueError("Unsupported image format or excessive dimensions")
            image.load()
            image.thumbnail((1280, 720))
            output = io.BytesIO()
            image.convert("RGB").save(output, format="JPEG", quality=80)
        with self._lock:
            self._check(token)  # An upload cannot revive a stopped session.
            self._frame = output.getvalue()
            self._frame_time = self._clock()
            return self.status()

    def image(self, token):
        with self._lock:
            self._check(token)
            self.status()
            if self._frame is None:
                raise ValueError("No fresh shared screen frame. Start sharing and try again.")
            return self._frame


active_desktop = ActiveDesktopSession()
