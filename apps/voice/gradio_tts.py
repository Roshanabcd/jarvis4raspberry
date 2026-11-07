"""
Custom Voice Cloning TTS Provider for JARVIS OS.
Integrates remote Gradio voice-cloning endpoints using gradio_client.
Features:
- Dynamic API schema discovery via client.view_api() (no hardcoded/guessed parameter indices).
- Resilient offline fallback to local TextToSpeech (espeak / pyttsx3 / simulated) when link expires or is unreachable.
- Disk-based audio phrase caching (avoids redundant synthesis requests).
- Safe file validation (RIFF / MP3 headers, size bounds) before playback.
- Playback synchronization lock to avoid overlapping audio corruption.
- Graceful cancellation and process cleanup.
"""

import os
import io
import time
import hashlib
import logging
import threading
import subprocess
import shutil
from dataclasses import dataclass
from typing import Optional, Dict, Any

from config.config_manager import config
from apps.voice.tts import TextToSpeech

logger = logging.getLogger("JARVIS.Voice.GradioTTS")


@dataclass
class AudioResult:
    """Represents synthesized audio result."""
    audio_path: Optional[str]
    format: str
    duration_s: float
    cached: bool
    provider: str
    text: str
    success: bool
    error: Optional[str] = None


class GradioVoiceCloner:
    """
    Custom voice-cloning TTS provider backed by a Gradio application.
    Implements:
    - synthesize(text, voice_config) -> AudioResult
    - play(audio_result)
    - stop_playback()
    - get_provider_status()
    """

    def __init__(
        self,
        gradio_url: Optional[str] = None,
        reference_voice_path: Optional[str] = None,
        cache_dir: Optional[str] = None,
        fallback_tts: Optional[TextToSpeech] = None,
    ):
        v_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
        self.gradio_url = (
            gradio_url
            or os.environ.get("GRADIO_VOICE_URL")
            or v_cfg.get("gradio_url", "https://13f7044a4e78090fd2.gradio.live/")
        ).strip()

        self.reference_voice_path = (
            reference_voice_path
            or os.environ.get("GRADIO_VOICE_SAMPLE")
            or v_cfg.get("reference_audio_path")
        )

        self.cache_dir = cache_dir or os.path.join(
            os.path.expanduser("~"), ".cache", "jarvis_voice_cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)

        self.fallback_tts = fallback_tts or TextToSpeech()

        self._client = None
        self._api_info: Optional[Dict[str, Any]] = None
        self._online: Optional[bool] = None
        self._last_probe: float = 0.0
        self._probe_interval: float = 60.0  # Probe at most once a minute

        self._playback_lock = threading.Lock()
        self._current_player: Optional[subprocess.Popen] = None

        logger.info(
            "GradioVoiceCloner initialized (url=%s, cache_dir=%s)",
            self.gradio_url, self.cache_dir
        )

    def _get_cache_path(self, text: str) -> str:
        """Generate deterministic cache filename based on text hash."""
        text_hash = hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.cache_dir, f"phrase_{text_hash}.wav")

    def _probe_gradio_client(self, force: bool = False) -> bool:
        """Inspect and connect to the remote Gradio instance without guessing."""
        now = time.time()
        if not force and self._online is not None and (now - self._last_probe < self._probe_interval):
            return bool(self._online)

        self._last_probe = now
        if not self.gradio_url or self.gradio_url.startswith("http://disabled"):
            self._online = False
            return False

        try:
            from gradio_client import Client
            logger.info("Connecting to Gradio voice cloner at: %s", self.gradio_url)
            self._client = Client(self.gradio_url)
            # Inspect endpoints dynamically without guessing
            try:
                self._api_info = self._client.view_api(return_format="dict")
                logger.info("Successfully fetched Gradio API schema: %s", list(self._api_info.get("named_endpoints", {}).keys()))
            except Exception as e:
                logger.debug("view_api returned: %s", e)
            self._online = True
            return True
        except Exception as exc:
            logger.warning(
                "Gradio voice server at '%s' is unavailable: %s. Using local TTS fallback.",
                self.gradio_url, exc
            )
            self._client = None
            self._online = False
            return False

    def get_provider_status(self) -> Dict[str, Any]:
        """Return provider connectivity and configuration status."""
        is_online = self._probe_gradio_client(force=False)
        return {
            "name": "gradio_voice_clone",
            "url": self.gradio_url,
            "online": is_online,
            "has_reference_audio": bool(self.reference_voice_path and os.path.exists(self.reference_voice_path)),
            "api_endpoints": list(self._api_info.get("named_endpoints", {}).keys()) if self._api_info else [],
            "fallback_backend": self.fallback_tts.backend,
            "cache_entries": len(os.listdir(self.cache_dir)) if os.path.exists(self.cache_dir) else 0,
        }

    def _validate_audio_file(self, file_path: str) -> bool:
        """Verify audio file exists, has content, and has valid header."""
        if not file_path or not os.path.exists(file_path):
            return False
        size = os.path.getsize(file_path)
        if size < 44:  # Smaller than minimal WAV header
            return False

        try:
            with open(file_path, "rb") as f:
                header = f.read(12)
            # Check for WAV (RIFF....WAVE) or MP3 (ID3 or 0xFFFB) or OGG (OggS) or FLAC
            if header[:4] == b"RIFF" and header[8:12] == b"WAVE":
                return True
            if header[:3] == b"ID3":
                return True
            if len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0:
                return True
            if header[:4] == b"OggS":
                return True
            if header[:4] == b"fLaC":
                return True
            return False
        except Exception:
            return False

    def synthesize(self, text: str, voice_config: Optional[Dict[str, Any]] = None) -> AudioResult:
        """
        Synthesize speech from text.
        Checks cache -> tries Gradio remote cloner -> falls back to local TTS.
        """
        if not text or not text.strip():
            return AudioResult(
                audio_path=None, format="none", duration_s=0.0,
                cached=False, provider="none", text="", success=False,
                error="Empty text"
            )

        clean_text = text.strip()
        cache_path = self._get_cache_path(clean_text)

        # 1. Cache hit check
        if os.path.exists(cache_path) and self._validate_audio_file(cache_path):
            logger.debug("Voice synthesis cache hit for: '%s'", clean_text[:40])
            return AudioResult(
                audio_path=cache_path,
                format="wav",
                duration_s=0.0,
                cached=True,
                provider="cache",
                text=clean_text,
                success=True,
            )

        # 2. Try Gradio remote synthesis if online
        if self._probe_gradio_client():
            try:
                result_audio_path = None
                # Check endpoints discovered from view_api
                named = self._api_info.get("named_endpoints", {}) if self._api_info else {}
                if "/predict" in named:
                    # Dynamically inspect parameter requirements
                    ep = named["/predict"]
                    params = ep.get("parameters", [])
                    args = []
                    for param in params:
                        label = (param.get("label") or param.get("name") or "").lower()
                        if "audio" in label or "voice" in label:
                            from gradio_client import handle_file
                            ref_path = self.reference_voice_path or cache_path
                            args.append(handle_file(ref_path) if os.path.exists(ref_path) else None)
                        elif "text" in label or "prompt" in label:
                            args.append(clean_text)
                        else:
                            args.append(param.get("default", None))
                    
                    job = self._client.predict(*args, api_name="/predict")
                    result_audio_path = job
                else:
                    # Default prediction if endpoint schema is generic
                    job = self._client.predict(clean_text)
                    result_audio_path = job

                if result_audio_path and self._validate_audio_file(result_audio_path):
                    shutil.copy2(result_audio_path, cache_path)
                    return AudioResult(
                        audio_path=cache_path,
                        format="wav",
                        duration_s=0.0,
                        cached=False,
                        provider="gradio_voice_clone",
                        text=clean_text,
                        success=True,
                    )
            except Exception as exc:
                logger.warning(
                    "Gradio voice synthesis failed: %s. Falling back to local TTS.",
                    exc
                )

        # 3. Fallback: Local TTS synthesis
        logger.info("[Gradio Offline/Fallback] Synthesizing via fallback TTS: '%s'", clean_text[:50])
        self.fallback_tts.speak_sync(clean_text)
        return AudioResult(
            audio_path=None,
            format="pcm",
            duration_s=0.0,
            cached=False,
            provider="fallback_local_tts",
            text=clean_text,
            success=True,
        )

    def play(self, audio_result: AudioResult) -> bool:
        """
        Play audio safely without concurrent playback corruption.
        """
        if not audio_result or not audio_result.success:
            return False

        # If audio_path is None, it was already spoken by fallback TTS
        if not audio_result.audio_path:
            return True

        with self._playback_lock:
            self.stop_playback()

            if not self._validate_audio_file(audio_result.audio_path):
                logger.error("Audio file validation failed: %s", audio_result.audio_path)
                return False

            player_bin = shutil.which("aplay") or shutil.which("paplay") or shutil.which("ffplay")
            if not player_bin:
                logger.warning("No audio playback binary found on system.")
                return False

            try:
                cmd = [player_bin, audio_result.audio_path]
                if "ffplay" in player_bin:
                    cmd.extend(["-nodisp", "-autoexit", "-loglevel", "quiet"])
                self._current_player = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self._current_player.wait(timeout=15)
                self._current_player = None
                return True
            except subprocess.TimeoutExpired:
                logger.warning("Audio playback timed out after 15 seconds.")
                self.stop_playback()
                return False
            except Exception as exc:
                logger.error("Error playing audio: %s", exc)
                return False

    def stop_playback(self) -> None:
        """Immediately halt currently playing audio."""
        if self._current_player and self._current_player.poll() is None:
            try:
                self._current_player.terminate()
                self._current_player.wait(timeout=1.0)
            except Exception:
                try:
                    self._current_player.kill()
                except Exception:
                    pass
            self._current_player = None


# Module-level default instance
gradio_cloner = GradioVoiceCloner()
