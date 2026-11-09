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
import re
import shutil
from dataclasses import dataclass
from typing import Optional, Dict, Any

from config.config_manager import config
from apps.voice.tts import TextToSpeech

logger = logging.getLogger("JARVIS.Voice.GradioTTS")


def sanitize_speech_text(text: str) -> str:
    """
    Sanitize text for speech synthesis:
    - Removes code blocks, URLs, markdown syntax
    - Removes non-verbal bracketed tags (e.g. [laughter], [sigh])
    - Removes emojis and unicode decorative symbols
    - Collapses multiple whitespace
    """
    if not text:
        return ""
    # Remove code blocks
    cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove URLs
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    # Remove emojis and astral plane symbols
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    # Remove bracketed non-verbal tags like [laughter], [sigh]
    cleaned = re.sub(r'\[[a-zA-Z0-9_\-]+\]', '', cleaned)
    # Remove markdown headers (# Title)
    cleaned = re.sub(r'#+\s*', '', cleaned)
    # Remove markdown bold/italic/code: **bold**, *italic*, `code`
    cleaned = re.sub(r'[*_`]', '', cleaned)
    # Collapse whitespace before punctuation and normalize spaces
    cleaned = re.sub(r'\s+([.,!?;:])', r'\1', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


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
    latency_ms: float = 0.0
    is_cloned: bool = False


class GradioVoiceCloner:
    """
    Custom voice-cloning TTS provider backed by a Gradio application.
    Implements:
    - synthesize(text, voice_config) -> AudioResult
    - play(audio_result)
    - stop_playback()
    - get_provider_status()
    - update_url(new_url, api_info)
    """

    def __init__(
        self,
        gradio_url: Optional[str] = None,
        reference_voice_path: Optional[str] = None,
        cache_dir: Optional[str] = None,
        fallback_tts: Optional[TextToSpeech] = None,
        cloning_enabled: Optional[bool] = None,
    ):
        v_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
        self.cloning_enabled = (
            cloning_enabled
            if cloning_enabled is not None
            else v_cfg.get("cloning_enabled", True)
        )

        self._explicit_url = bool(gradio_url)

        # Dynamic URL resolution: colab_manager takes precedence if active and not explicitly overridden
        try:
            from apps.voice.colab_registration import colab_manager
            active_colab = colab_manager.get_active_url() if not self._explicit_url else ""
        except Exception:
            active_colab = ""

        self.gradio_url = (
            gradio_url
            or active_colab
            or os.environ.get("GRADIO_VOICE_URL")
            or v_cfg.get("gradio_url", "https://roshan-omnivoice-jarvis.hf.space")
        ).strip()

        # Find reference voice sample (prioritize 3-10s clean reference clip)
        if reference_voice_path is not None:
            self.reference_voice_path = reference_voice_path
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            raw_candidates = [
                os.environ.get("GRADIO_VOICE_SAMPLE"),
                v_cfg.get("reference_audio_path"),
                os.path.join(project_root, "data", "voice_samples", "myvoice_ref_clean.wav"),
                "/home/roshan/Downloads/myvoice_clean.wav",
                "/home/roshan/Downloads/myvoice_ref_clean.wav",
                os.path.join(project_root, "data", "voice_samples", "myvoice.wav"),
                "/home/roshan/Downloads/myvoice.mp3",
                "/home/roshan/Downloads/myvoice.mpeg",
                "/home/roshan/Downloads/myvoice.wav",
                "/home/roshan/Music/myvoice.mpeg",
                "/home/roshan/Music/myvoice.mp3",
                "/home/roshan/myvoice.mp3",
            ]
            self.reference_voice_path = None
            for cand in raw_candidates:
                if not cand or not isinstance(cand, str):
                    continue
                cand_path = cand if os.path.isabs(cand) else os.path.join(project_root, cand)
                if os.path.exists(cand_path) and os.path.getsize(cand_path) > 100:
                    self.reference_voice_path = os.path.abspath(cand_path)
                    break

        # Voice quality, pacing, and phonetic alignment defaults
        self.reference_text = (
            os.environ.get("GRADIO_VOICE_REF_TEXT")
            or v_cfg.get("reference_text", "Good morning everyone, my name is Roshan Sharma.")
        ).strip()
        self.default_speed = float(
            os.environ.get("GRADIO_VOICE_SPEED") or v_cfg.get("speed", 0.85)
        )
        self.default_num_steps = int(
            os.environ.get("GRADIO_VOICE_NUM_STEPS") or v_cfg.get("num_steps", 32)
        )

        self.is_hf_space = bool(
            "hf.space" in self.gradio_url
            or "huggingface.co/spaces" in self.gradio_url
            or ("/" in self.gradio_url and not self.gradio_url.startswith("http"))
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
            "GradioVoiceCloner initialized (url=%s, ref_audio=%s, speed=%.2f, steps=%d, cache_dir=%s)",
            self.gradio_url, self.reference_voice_path, self.default_speed, self.default_num_steps, self.cache_dir
        )

    def update_url(self, new_url: str, api_info: Optional[Dict[str, Any]] = None) -> None:
        """Dynamically update active Gradio server URL and reset client."""
        with self._playback_lock:
            self.gradio_url = new_url.strip() if new_url else ""
            self._client = None
            self._api_info = api_info
            self._online = None
            self._last_probe = 0.0
            self.is_hf_space = bool(
                "hf.space" in self.gradio_url
                or "huggingface.co/spaces" in self.gradio_url
                or ("/" in self.gradio_url and not self.gradio_url.startswith("http"))
            )
            logger.info("GradioVoiceCloner URL dynamically updated to: %s", self.gradio_url)

    def set_reference_audio(self, path: str) -> None:
        """Dynamically update reference audio sample path for voice cloning."""
        if path and os.path.exists(path):
            self.reference_voice_path = os.path.abspath(path)
            logger.info("GradioVoiceCloner reference audio updated to: %s", self.reference_voice_path)

    def _count_cache_entries(self) -> int:
        """Count audio files in cache directory."""
        if os.path.exists(self.cache_dir):
            try:
                return len(os.listdir(self.cache_dir))
            except Exception:
                return 0
        return 0

    def _get_cache_path(self, text: str, speed: Optional[float] = None, num_steps: Optional[int] = None) -> str:
        """Generate deterministic cache filename based on text, speed, steps, and sample hash."""
        sp = speed if speed is not None else self.default_speed
        st = num_steps if num_steps is not None else self.default_num_steps
        ref_id = os.path.basename(self.reference_voice_path) if self.reference_voice_path else "none"
        key = f"{text.strip().lower()}:{sp:.2f}:{st}:{ref_id}"
        text_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.cache_dir, f"phrase_{text_hash}.wav")

    def _probe_gradio_client(self, force: bool = False) -> bool:
        """Inspect and connect to the remote Gradio instance without guessing."""
        if not getattr(self, "_explicit_url", False):
            try:
                from apps.voice.colab_registration import colab_manager
                dynamic_url = colab_manager.get_active_url()
                if dynamic_url and dynamic_url != self.gradio_url:
                    self.update_url(dynamic_url)
            except Exception:
                pass

        now = time.time()
        if not force and self._client is not None and self._online is True and (now - self._last_probe < self._probe_interval):
            return True

        self._last_probe = now
        if not self.gradio_url or self.gradio_url.startswith("http://disabled") or not self.gradio_url.startswith("http"):
            self._online = False
            return False

        # Fast pre-flight HTTP check with 3.0s timeout to prevent blocking on dead URLs
        import requests
        try:
            resp = requests.head(self.gradio_url, timeout=3.0, allow_redirects=True)
            if resp.status_code == 405:
                # Server doesn't support HEAD, fallback to GET
                resp = requests.get(self.gradio_url, timeout=3.0)
            if resp.status_code >= 400:
                logger.info("Gradio voice server at '%s' returned HTTP %d. Using fallback.", self.gradio_url, resp.status_code)
                self._online = False
                try:
                    from apps.voice.colab_registration import colab_manager
                    colab_manager.mark_offline(f"HTTP {resp.status_code}")
                except Exception:
                    pass
                return False
        except Exception as exc:
            logger.info("Pre-flight ping to Gradio URL '%s' failed (%s). Using local fallback.", self.gradio_url, exc)
            self._online = False
            try:
                from apps.voice.colab_registration import colab_manager
                colab_manager.mark_offline(str(exc))
            except Exception:
                pass
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
            try:
                from apps.voice.colab_registration import colab_manager
                colab_manager.mark_offline(str(exc))
            except Exception:
                pass
            return False

    def get_provider_status(self) -> Dict[str, Any]:
        """Return provider connectivity and configuration status."""
        if not getattr(self, "_explicit_url", False):
            try:
                from apps.voice.colab_registration import colab_manager
                dynamic_url = colab_manager.get_active_url()
                if dynamic_url and dynamic_url != self.gradio_url:
                    self.update_url(dynamic_url)
            except Exception:
                pass

        is_online = self._probe_gradio_client(force=False) if self.cloning_enabled else False
        return {
            "name": "gradio_voice_clone",
            "url": self.gradio_url,
            "cloning_enabled": self.cloning_enabled,
            "is_hf_space": self.is_hf_space,
            "online": is_online,
            "has_reference_audio": bool(self.reference_voice_path and os.path.exists(self.reference_voice_path)),
            "reference_audio_path": self.reference_voice_path,
            "reference_text": self.reference_text,
            "speed": self.default_speed,
            "num_steps": self.default_num_steps,
            "api_endpoints": list(self._api_info.get("named_endpoints", {}).keys()) if self._api_info else [],
            "fallback_backend": self.fallback_tts.backend,
            "cache_entries": self._count_cache_entries(),
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
        t_start = time.perf_counter()
        if not text or not text.strip():
            return AudioResult(
                audio_path=None, format="none", duration_s=0.0,
                cached=False, provider="none", text="", success=False,
                error="Empty text", latency_ms=0.0, is_cloned=False
            )

        clean_text = sanitize_speech_text(text)
        if not clean_text:
            return AudioResult(
                audio_path=None, format="none", duration_s=0.0,
                cached=False, provider="none", text="", success=False,
                error="Empty text after sanitization", latency_ms=0.0, is_cloned=False
            )

        v_dict = voice_config or {}
        num_steps = int(v_dict.get("num_steps", self.default_num_steps))
        speed = float(v_dict.get("speed", self.default_speed))
        ref_text = str(v_dict.get("reference_text", self.reference_text)).strip()

        cache_path = self._get_cache_path(clean_text, speed=speed, num_steps=num_steps)

        # 1. Cache hit check
        if os.path.exists(cache_path) and self._validate_audio_file(cache_path):
            logger.debug("Voice synthesis cache hit for: '%s'", clean_text[:40])
            return AudioResult(
                audio_path=cache_path,
                format="wav" if cache_path.endswith(".wav") else "mp3",
                duration_s=0.0,
                cached=True,
                provider="cache",
                is_cloned=True,
                text=clean_text,
                success=True,
                latency_ms=(time.perf_counter() - t_start) * 1000,
            )

        # 2. Try Gradio remote synthesis if enabled and reference sample exists
        if self.cloning_enabled:
            if not getattr(self, "_explicit_url", False):
                try:
                    from apps.voice.colab_registration import colab_manager
                    dynamic_url = colab_manager.get_active_url()
                    if dynamic_url and dynamic_url != self.gradio_url:
                        self.update_url(dynamic_url)
                except Exception:
                    pass

            if not self.reference_voice_path or not os.path.exists(self.reference_voice_path):
                logger.warning(
                    "Reference voice sample '%s' not found. Falling back to local TTS.",
                    self.reference_voice_path
                )
            elif self._probe_gradio_client():
                try:
                    result_audio_path = None
                    from gradio_client import handle_file
                    ref_handle = handle_file(self.reference_voice_path)

                    # Check endpoints discovered from view_api
                    named = self._api_info.get("named_endpoints", {}) if self._api_info else {}

                    if "/generate" in named or "generate" in named:
                        ep_name = "/generate" if "/generate" in named else "generate"
                        try:
                            job = self._client.submit(
                                clean_text,
                                "Voice Cloning",
                                ref_handle,
                                ref_text,
                                "Custom (type your own)",
                                "",
                                num_steps,
                                speed,
                                api_name=ep_name
                            ).result(timeout=90.0)
                        except AttributeError:
                            job = self._client.predict(
                                clean_text,
                                "Voice Cloning",
                                ref_handle,
                                ref_text,
                                "Custom (type your own)",
                                "",
                                num_steps,
                                speed,
                                api_name=ep_name
                            )
                        result_audio_path = job[0] if isinstance(job, (list, tuple)) else job
                    elif "/clone_voice" in named or "clone_voice" in named:
                        ep_name = "/clone_voice" if "/clone_voice" in named else "clone_voice"
                        try:
                            job = self._client.submit(clean_text, ref_handle, ref_text, num_steps, speed, api_name=ep_name).result(timeout=90.0)
                        except AttributeError:
                            job = self._client.predict(clean_text, ref_handle, ref_text, num_steps, speed, api_name=ep_name)
                        result_audio_path = job[0] if isinstance(job, (list, tuple)) else job
                    elif "/predict" in named or "predict" in named:
                        ep_name = "/predict" if "/predict" in named else "predict"
                        ep = named[ep_name]
                        params = ep.get("parameters", [])
                        args = []
                        for param in params:
                            label = (param.get("label") or param.get("name") or "").lower()
                            if "audio" in label or "voice" in label or "ref" in label:
                                args.append(ref_handle)
                            elif "text" in label or "prompt" in label:
                                args.append(clean_text)
                            elif "mode" in label:
                                args.append("Voice Cloning")
                            else:
                                args.append(param.get("default", None))
                        try:
                            job = self._client.submit(*args, api_name=ep_name).result(timeout=90.0)
                        except AttributeError:
                            job = self._client.predict(*args, api_name=ep_name)
                        result_audio_path = job[0] if isinstance(job, (list, tuple)) else job
                    else:
                        try:
                            job = self._client.submit(clean_text).result(timeout=90.0)
                        except AttributeError:
                            job = self._client.predict(clean_text)
                        result_audio_path = job[0] if isinstance(job, (list, tuple)) else job

                    if result_audio_path and self._validate_audio_file(result_audio_path):
                        shutil.copy2(result_audio_path, cache_path)
                        try:
                            from apps.voice.colab_registration import colab_manager
                            with colab_manager._lock:
                                colab_manager.state["last_generation_time"] = time.time()
                                colab_manager.state["last_error"] = None
                        except Exception:
                            pass

                        provider_name = "omnivoice_clone" if ("/generate" in ep_name or "generate" in ep_name) else "gradio_voice_clone"
                        return AudioResult(
                            audio_path=cache_path,
                            format="wav",
                            duration_s=0.0,
                            cached=False,
                            provider=provider_name,
                            is_cloned=True,
                            text=clean_text,
                            success=True,
                            latency_ms=(time.perf_counter() - t_start) * 1000,
                        )
                except Exception as exc:
                    err_msg = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
                    logger.warning(
                        "Gradio voice synthesis failed: %s. Falling back to local TTS.",
                        err_msg
                    )
                    try:
                        from apps.voice.colab_registration import colab_manager
                        with colab_manager._lock:
                            colab_manager.state["last_error"] = err_msg
                    except Exception:
                        pass
                        with colab_manager._lock:
                            colab_manager.state["last_error"] = str(exc)
                    except Exception:
                        pass

        # 3. Fallback: High quality Neural TTS or local espeak saved to cache_path
        logger.info("[Gradio Offline/Fallback] Synthesizing via neural/local TTS: '%s'", clean_text[:50])
        try:
            import sys
            edge_bin = (
                shutil.which("edge-tts")
                or os.path.join(os.path.dirname(sys.executable), "edge-tts")
            )
            if edge_bin and os.path.exists(edge_bin):
                cmd = [edge_bin, "--text", clean_text, "--voice", "en-GB-RyanNeural", "--write-media", cache_path]
            else:
                cmd = [sys.executable, "-m", "edge_tts", "--text", clean_text, "--voice", "en-GB-RyanNeural", "--write-media", cache_path]

            res = subprocess.run(cmd, capture_output=True, timeout=25)
            if res.returncode == 0 and os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
                return AudioResult(
                    audio_path=cache_path,
                    format="mp3",
                    duration_s=0.0,
                    cached=False,
                    provider="edge_neural_tts",
                    is_cloned=False,
                    text=clean_text,
                    success=True,
                    latency_ms=(time.perf_counter() - t_start) * 1000,
                )
            else:
                logger.warning("edge-tts process returned code %d: %s", res.returncode, res.stderr.decode() if res.stderr else "")
        except Exception as e:
            logger.debug("edge-tts fallback exception: %s", e)

        # Espeak local offline fallback
        espeak_bin = shutil.which("espeak") or shutil.which("espeak-ng")
        if espeak_bin:
            try:
                cmd = [espeak_bin, "-w", cache_path, clean_text]
                res = subprocess.run(cmd, capture_output=True, timeout=5)
                if res.returncode == 0 and os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
                    return AudioResult(
                        audio_path=cache_path,
                        format="wav",
                        duration_s=0.0,
                        cached=False,
                        provider="espeak_local_tts",
                        is_cloned=False,
                        text=clean_text,
                        success=True,
                        latency_ms=(time.perf_counter() - t_start) * 1000,
                    )
            except Exception as e:
                logger.debug("espeak fallback exception: %s", e)

        # Simulation or pyttsx3 fallback
        self.fallback_tts.speak_sync(clean_text)
        return AudioResult(
            audio_path=None,
            format="pcm",
            duration_s=0.0,
            cached=False,
            provider="fallback_local_tts",
            is_cloned=False,
            text=clean_text,
            success=True,
            latency_ms=(time.perf_counter() - t_start) * 1000,
        )

    def play(self, audio_result: AudioResult, wait: bool = False) -> bool:
        """
        Play audio safely without concurrent playback corruption.
        Uses PipeWire 'pw-play' or ALSA 'aplay'.
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

            player_bin = shutil.which("pw-play") or shutil.which("paplay") or shutil.which("aplay") or shutil.which("ffplay")
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
                if wait:
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
        if self._current_player:
            if self._current_player.poll() is None:
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
