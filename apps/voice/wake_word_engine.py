"""
Wake Word & VAD Silence Engine for JARVIS OS.
Implements a 12-state explicit state machine, acoustic keyword detection
for 'Wake up JARVIS' / 'JARVIS', continuous audio capture, adaptive noise floor
estimation, 3.0-second silence detection via dynamic RMS energy, automatic command
submission, TTS feedback loop elimination, and a 15-second follow-up conversation window.
"""
from __future__ import annotations

import logging
import math
import os
import re
import signal
import struct
import subprocess
import sys
import threading
import tempfile
import time
import wave
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger("JARVIS-WAKE-ENGINE")


class WakeState(str, Enum):
    """The 12 formal states of the JARVIS Voice Assistant lifecycle."""
    DISABLED = "DISABLED"
    STANDBY_LISTENING = "STANDBY_LISTENING"
    WAKE_DETECTED = "WAKE_DETECTED"
    LISTENING_SPEECH = "LISTENING_SPEECH"
    STREAMING_TRANSCRIPTION = "STREAMING_TRANSCRIPTION"
    SILENCE_COUNTDOWN = "SILENCE_COUNTDOWN"
    COMMAND_SUBMITTED = "COMMAND_SUBMITTED"
    PROCESSING_AGENT = "PROCESSING_AGENT"
    SPEAKING_RESPONSE = "SPEAKING_RESPONSE"
    FOLLOW_UP_STANDBY = "FOLLOW_UP_STANDBY"
    MUTED = "MUTED"
    ERROR = "ERROR"


WAKE_PHRASES = [
    r"\bwake\s+up\s+jarvis\b",
    r"\bwake\s+up[,\s]+jarvis\b",
    r"\bhey\s+jarvis\b",
    r"\bok\s+jarvis\b",
    r"\bhello\s+jarvis\b",
    r"\bjarvis\b",
    r"\bjarves\b",
    r"\bjavis\b",
]


def is_voice_service_daemon_running() -> bool:
    """Check if the dedicated background systemd user service is currently active."""
    # System units running as the user often lack the user-bus environment.
    # Query the same user's daemon instead of treating a missing bus as no owner.
    runtime_dir = f"/run/user/{os.getuid()}"
    env = {**os.environ, "XDG_RUNTIME_DIR": runtime_dir,
           "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_dir}/bus"}
    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-active", "jarvis-voice.service"],
            capture_output=True,
            text=True,
            check=False,
            timeout=1.5,
            env=env,
        )
        state = res.stdout.strip()
        if state in {"active", "activating", "reloading", "deactivating"}:
            return True
        if state in {"inactive", "failed", "unknown"}:
            return False
        raise RuntimeError("Cannot determine the existing microphone owner")
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Cannot determine the existing microphone owner") from exc


class WakeWordEngine:
    """Coordinates the 12-state audio loop with adaptive noise floor and silence-driven dispatch."""

    def __init__(
        self,
        wake_phrases: Optional[List[str]] = None,
        silence_timeout_s: float = 3.0,
        follow_up_window_s: float = 15.0,
        energy_threshold: float = 120.0,
        temp_dir: str = "/tmp/jarvis_voice",
    ) -> None:
        try:
            from config.config_manager import config
            v_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
        except Exception:
            v_cfg = {}
        self.wake_phrases = wake_phrases or WAKE_PHRASES
        self.silence_timeout_s = float(v_cfg.get("silence_threshold_s", silence_timeout_s))
        self.follow_up_window_s = follow_up_window_s
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)

        # Dynamic / Adaptive noise floor parameters
        self.ambient_noise_floor: float = float(v_cfg.get("ambient_noise_floor", 40.0))
        self.adaptive_threshold: float = float(v_cfg.get("energy_threshold", energy_threshold))
        self.min_energy_threshold: float = float(v_cfg.get("min_energy_threshold", 90.0))
        self.max_energy_threshold: float = float(v_cfg.get("max_energy_threshold", 5000.0))
        self.wake_word_enabled: bool = True
        self._wake_threshold: float = float(v_cfg.get("wake_threshold", 0.5))
        self.wake_model_name: str = "hey_jarvis_v0.1"
        self._openwakeword_model: Optional[Any] = None
        self._prev_standby_frames: Optional[bytes] = None
        self._device_consecutive_errors: int = 0
        self._recorder_consecutive_failures: int = 0
        self._last_capture_time: float = 0.0
        self._last_audio_rms: Optional[float] = None
        self._capture_status = "waiting"
        self._recorder_exit_code = None
        self._capture_failure_reason = 'none'

        self._state: WakeState = WakeState.DISABLED
        self._is_running: bool = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._state_lock = threading.RLock()

        # State timestamps & metrics
        self._state_entered_time: float = time.time()
        self._last_speech_time: float = 0.0
        self._follow_up_deadline: float = 0.0
        self._current_transcript: str = ""
        self._last_command: str = ""
        self._last_response: str = ""
        self._last_error: Optional[str] = None

        # Command callback
        self._on_command_handler: Optional[Callable[[str], Any]] = None
        self._stt: Optional[Any] = None

    @property
    def stt(self):
        if self._stt is None:
            try:
                from apps.voice.stt import SpeechToText
                self._stt = SpeechToText(simulation_mode=False)
            except Exception as e:
                logger.error("Failed to initialize STT: %s", e)
        return self._stt

    @property
    def energy_threshold(self) -> float:
        """Dynamic energy threshold based on current ambient noise floor."""
        return self.adaptive_threshold

    @property
    def state(self) -> WakeState:
        with self._state_lock:
            return self._state

    def set_state(self, new_state: WakeState) -> None:
        with self._state_lock:
            if self._state != new_state:
                logger.info("WakeWordEngine State Transition: %s -> %s", self._state.value, new_state.value)
                self._state = new_state
                self._state_entered_time = time.time()
                try:
                    from apps.voice.daemon_status import publish_status
                    publish_status(self._state.value, self._is_running, diagnostics=self.get_capture_diagnostics())
                except Exception:
                    pass

    def set_command_handler(self, handler: Callable[[str], Any]) -> None:
        self._on_command_handler = handler

    def get_status(self) -> Dict[str, Any]:
        """Return full telemetry dictionary for the dashboard status indicator."""
        with self._state_lock:
            now = time.time()
            elapsed_in_state = round(now - self._state_entered_time, 2)
            follow_up_remaining = max(0.0, round(self._follow_up_deadline - now, 1)) if self._state == WakeState.FOLLOW_UP_STANDBY else 0.0

            try:
                from apps.voice.session_manager import voice_session_mgr
                session_data = voice_session_mgr.get_active_session().model_dump()
            except Exception:
                session_data = {"user_id": "guest", "display_name": "Guest", "role": "GUEST"}

            stt_lang = self.stt.get_language() if self.stt and hasattr(self.stt, "get_language") else "en-US"

            return {
                "state": self._state.value,
                "is_running": self._is_running,
                "wake_word_enabled": self.wake_word_enabled,
                "language": stt_lang,
                "session": session_data,
                "elapsed_in_state_s": elapsed_in_state,
                "follow_up_remaining_s": follow_up_remaining,
                "silence_timeout_s": self.silence_timeout_s,
                "follow_up_window_s": self.follow_up_window_s,
                "ambient_noise_floor_rms": round(self.ambient_noise_floor, 2),
                "adaptive_threshold_rms": round(self.adaptive_threshold, 2),
                "current_transcript": self._current_transcript,
                "last_command": self._last_command,
                "last_response": self._last_response,
                "error": self._last_error,
                **self.get_capture_diagnostics(),
            }

    def get_capture_diagnostics(self) -> Dict[str, Any]:
        """Numeric capture health only; never persist audio, text, or identity."""
        return {
            "capture_status": self._capture_status,
            "recorder_exit_code": self._recorder_exit_code,
            "capture_failure_reason": self._capture_failure_reason,
            "last_capture_age_s": round(max(0.0, time.monotonic() - self._last_capture_time), 1) if self._last_capture_time else None,
            "audio_level_rms": round(self._last_audio_rms, 2) if self._last_audio_rms is not None else None,
            "energy_threshold_rms": round(self.adaptive_threshold, 2),
            "recorder_failures": self._recorder_consecutive_failures,
            "stt_status": getattr(self._stt, "last_status", "idle"),
            "wake_word_enabled": self.wake_word_enabled,
            "wake_engine": "openwakeword",
            "wake_model": self.wake_model_name,
            "wake_threshold": self._wake_threshold,
        }

    def start(self) -> None:
        """Start the background voice assistant daemon thread."""
        with self._state_lock:
            if self._is_running:
                logger.warning("WakeWordEngine already running.")
                return

            self._is_running = True
            self._stop_event.clear()
            self.set_state(WakeState.STANDBY_LISTENING)

            self._thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="JARVIS-WakeWordEngine",
            )
            self._thread.start()
            logger.info("WakeWordEngine started in background.")

    def run_forever(self) -> None:
        """Run the wake word loop synchronously in the main thread until terminated."""
        def sig_handler(sig, frame):
            logger.info("Signal %s received. Stopping WakeWordEngine...", sig)
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

        logger.info("WakeWordEngine run_forever starting on PID %d...", os.getpid())
        with self._state_lock:
            self._is_running = True
            self._stop_event.clear()
            self.set_state(WakeState.STANDBY_LISTENING)

        def publish_telemetry():
            from apps.voice.daemon_status import publish_status
            while not self._stop_event.is_set():
                try:
                    publish_status(self.state.value, self._is_running, diagnostics=self.get_capture_diagnostics())
                except OSError:
                    logger.warning("Could not publish voice daemon telemetry")
                self._stop_event.wait(2.0)
            try:
                publish_status(WakeState.DISABLED.value, False)
            except OSError:
                pass

        telemetry = threading.Thread(target=publish_telemetry, daemon=True, name="VoiceTelemetry")
        telemetry.start()
        try:
            self._run_loop()
        finally:
            self._is_running = False
            self._stop_event.set()
            telemetry.join(timeout=3)

    def stop(self) -> None:
        """Stop the background voice assistant."""
        with self._state_lock:
            self._is_running = False
            self._stop_event.set()
            self.set_state(WakeState.DISABLED)
        thread = self._thread
        if thread and thread is not threading.current_thread() and thread.is_alive():
            thread.join(timeout=2.0)
        if thread is threading.current_thread():
            self._thread = None
        logger.info("WakeWordEngine stopped.")

    def mute(self) -> None:
        """Temporarily mute listening."""
        self.set_state(WakeState.MUTED)

    def unmute(self) -> None:
        """Unmute listening back to standby."""
        self.set_state(WakeState.STANDBY_LISTENING)

    def set_wake_word_enabled(self, enabled: bool) -> None:
        """Toggle automatic wake-word detection."""
        with self._state_lock:
            self.wake_word_enabled = bool(enabled)
            logger.info("Wake word detection enabled: %s", self.wake_word_enabled)

    def set_silence_timeout(self, timeout_s: float) -> None:
        """Update continuous silence duration threshold."""
        with self._state_lock:
            if 0.5 <= timeout_s <= 10.0:
                self.silence_timeout_s = float(timeout_s)
                logger.info("Silence timeout updated to %.1fs", self.silence_timeout_s)

    def set_vad_sensitivity(self, level: str) -> None:
        """Adjust VAD sensitivity (low, medium, high)."""
        with self._state_lock:
            lvl = level.lower().strip()
            if lvl == "high":
                self.min_energy_threshold = 100.0
                self.adaptive_threshold = max(100.0, self.ambient_noise_floor * 1.4)
                self._wake_threshold = 0.35
            elif lvl == "low":
                self.min_energy_threshold = 300.0
                self.adaptive_threshold = max(300.0, self.ambient_noise_floor * 2.5)
                self._wake_threshold = 0.70
            else:  # medium / default
                self.min_energy_threshold = 150.0
                self.adaptive_threshold = max(150.0, self.ambient_noise_floor * 1.8)
                self._wake_threshold = 0.50
            self.adaptive_threshold = min(self.adaptive_threshold, self.max_energy_threshold)
            logger.info("VAD sensitivity configured to %s (threshold: %.1f, wake_threshold: %.2f)",
                        lvl, self.adaptive_threshold, self._wake_threshold)

    def set_wake_threshold(self, threshold: float) -> None:
        """Directly adjust acoustic wake-word confidence threshold."""
        with self._state_lock:
            self._wake_threshold = max(0.05, min(0.99, float(threshold)))
            logger.info("Acoustic wake threshold set to %.2f", self._wake_threshold)

    def _score_acoustic_wake(self, wav_path: str) -> float:
        """Score audio chunk using local openWakeWord neural model for 'hey_jarvis' / 'jarvis'."""
        if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
            return 0.0
        try:
            if self._openwakeword_model is None:
                import openwakeword
                from openwakeword.model import Model
                paths = [p for p in openwakeword.get_pretrained_model_paths() if "hey_jarvis" in p]
                if not paths:
                    paths = openwakeword.get_pretrained_model_paths()
                self._openwakeword_model = Model(wakeword_model_paths=paths)

            with wave.open(wav_path, "rb") as wf:
                raw_frames = wf.readframes(wf.getnframes())
                if not raw_frames:
                    return 0.0
                import numpy as np
                audio_data = np.frombuffer(raw_frames, dtype=np.int16)

            max_score = 0.0
            step = 1280
            for i in range(0, len(audio_data) - step + 1, step):
                pred = self._openwakeword_model.predict(audio_data[i:i + step])
                for k, v in pred.items():
                    if v > max_score:
                        max_score = v
            return float(max_score)
        except Exception as e:
            logger.debug("Acoustic wake word scoring error: %s", e)
            return 0.0

    def barge_in(self) -> None:
        """Immediately halt active speech playback and transition to listening."""
        with self._state_lock:
            try:
                from apps.voice.speech_manager import speech_manager
                speech_manager.stop()
            except Exception as e:
                logger.debug("barge_in stop_playback error: %s", e)
            logger.info("Barge-in activated. Speech playback stopped.")
            self._current_transcript = ""
            self._last_speech_time = time.time()
            self.set_state(WakeState.LISTENING_SPEECH)

    def trigger_push_to_talk(self) -> None:
        """Directly activate voice command listening without waiting for wake word."""
        with self._state_lock:
            self.barge_in()
            logger.info("Push-to-Talk manually activated.")

    def _calculate_audio_rms(self, wav_path: str) -> float:
        """Calculate Root Mean Square audio amplitude for voice energy detection."""
        if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
            return 0.0
        try:
            with wave.open(wav_path, "rb") as wf:
                n_frames = wf.getnframes()
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                if n_frames == 0 or channels <= 0 or sample_width != 2:
                    return 0.0
                raw_bytes = wf.readframes(n_frames)
                fmt = f"<{n_frames * channels}h"
                samples = struct.unpack(fmt, raw_bytes)
                sum_sq = sum(s * s for s in samples)
                return math.sqrt(sum_sq / max(1, len(samples)))
        except Exception as e:
            logger.debug("RMS calculation error on %s: %s", wav_path, e)
            return 0.0

    def _get_recorder_backoff_delay(self) -> float:
        """Calculate exponential backoff delay when recording device is unavailable."""
        if self._recorder_consecutive_failures <= 0:
            return 0.05
        return min(4.0, 0.5 * (1.5 ** min(self._recorder_consecutive_failures, 6)))

    def _record_audio_chunk(self, output_path: str, duration_s: float = 1.5) -> bool:
        """Record audio chunk using pw-record with PipeWire default source."""
        started_at = time.time()
        self._capture_status = "recording"
        self._capture_failure_reason = 'none'
        try:
            os.unlink(output_path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            logger.warning("Could not remove stale audio chunk %s: %s", output_path, exc)
            self._recorder_consecutive_failures += 1
            self._capture_status = "failed"
            self._capture_failure_reason = 'file_cleanup_failed'
            return False

        proc = None
        try:
            cmd = ["pw-record", "--rate=16000", "--channels=1", "--format=s16", output_path]
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(duration_s)
            stopped_by_us = proc.poll() is None
            if stopped_by_us:
                proc.terminate()
            try:
                proc.communicate(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()

            self._recorder_exit_code = proc.returncode
            # PipeWire can exit 1 on a requested SIGTERM after successfully
            # finalizing the WAV. Never accept an early exit or an invalid file.
            acceptable_exit = proc.returncode in (0, -signal.SIGTERM) or (stopped_by_us and proc.returncode == 1)
            if not acceptable_exit:
                self._recorder_consecutive_failures += 1
                self._capture_status = "failed"
                self._capture_failure_reason = 'recorder_exit'
                if self._recorder_consecutive_failures <= 3 or self._recorder_consecutive_failures % 15 == 0:
                    logger.warning("pw-record exited with status %s (consecutive failures: %d)",
                                   proc.returncode, self._recorder_consecutive_failures)
                return False

            success = (
                os.path.isfile(output_path)
                and os.path.getsize(output_path) > 300
                and os.path.getmtime(output_path) >= started_at
            )
            if success:
                try:
                    with wave.open(output_path, 'rb') as audio:
                        success = (audio.getnchannels() == 1 and audio.getsampwidth() == 2
                                   and audio.getframerate() == 16000 and audio.getnframes() > 0
                                   and audio.getnframes() / 16000 >= max(0, duration_s * 0.25))
                except (OSError, EOFError, wave.Error):
                    success = False
            if success:
                self._recorder_consecutive_failures = 0
                self._last_capture_time = time.monotonic()
                self._last_audio_rms = self._calculate_audio_rms(output_path)
                self._capture_status = "ok"
            else:
                self._recorder_consecutive_failures += 1
                self._capture_status = "failed"
                self._capture_failure_reason = 'empty_or_stale_file'
            return success
        except Exception as e:
            self._recorder_consecutive_failures += 1
            self._capture_status = "failed"
            self._capture_failure_reason = 'recorder_exception'
            logger.error("Audio recording error: %s", e)
            if proc is not None and proc.poll() is None:
                proc.kill()
                proc.wait()
            return False

    def _transcribe(self, wav_path: str, fallback_to_whisper: Optional[bool] = None) -> str:
        """Transcribe an audio chunk using real speech recognition without mock data."""
        try:
            if self.stt:
                if fallback_to_whisper is None:
                    # In standby listening, skip slow CPU Whisper if cloud STT reports unintelligible speech
                    fallback_to_whisper = (self.state != WakeState.STANDBY_LISTENING)
                text = self.stt.transcribe(wav_path, fallback_to_whisper=fallback_to_whisper)
                return text.strip() if text else ""
            return ""
        except Exception as e:
            logger.error("STT transcription failure: %s", e)
            return ""

    def _matches_wake_phrase(self, text: str) -> bool:
        """Check if transcribed phrase matches any configured wake phrase patterns."""
        if not text:
            return False
        clean = text.lower().strip()
        for pat in self.wake_phrases:
            if re.search(pat, clean):
                return True
        return False

    def _command_after_wake_phrase(self, text: str) -> str:
        """Keep commands spoken in the same breath as the wake phrase."""
        for pattern in self.wake_phrases:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return text[match.end():].lstrip(" ,.!?:;-").strip()
        return ""

    def _is_tts_playing(self, playback_path: Optional[Any] = None) -> bool:
        """Check if JARVIS physical speaker is currently outputting speech (prevents acoustic feedback).

        Checks both in-process speech manager and cross-process active playback leases.
        """
        try:
            from apps.voice.playback_state import is_playback_active
            return is_playback_active(path=playback_path)
        except Exception:
            try:
                from apps.voice.speech_manager import speech_manager
                return speech_manager.is_playing()
            except Exception:
                return False

    def _check_daemon_commands(self) -> None:
        """Poll and execute cross-process control directives sent to this daemon."""
        try:
            from apps.voice.daemon_control import poll_daemon_command
            cmd = poll_daemon_command()
            if cmd == "mute":
                logger.info("Executing cross-process mute command.")
                self.mute()
            elif cmd == "unmute":
                logger.info("Executing cross-process unmute command.")
                self.unmute()
            elif cmd == "stop":
                logger.info("Executing cross-process stop command.")
                self.stop()
            elif cmd == "barge_in":
                logger.info("Executing cross-process barge_in command.")
                self.barge_in()
            elif cmd == "push_to_talk":
                logger.info("Executing cross-process push_to_talk command.")
                self.trigger_push_to_talk()
            elif cmd == "wake_enable":
                logger.info("Executing cross-process wake_enable command.")
                self.set_wake_word_enabled(True)
            elif cmd == "wake_disable":
                logger.info("Executing cross-process wake_disable command.")
                self.set_wake_word_enabled(False)
        except Exception as exc:
            logger.debug("Error checking daemon commands: %s", exc)

    def _update_adaptive_threshold(self, rms: float, is_speech: bool = False) -> None:
        """Smoothly calibrate noise floor and compute dynamic energy threshold."""
        if not is_speech and rms > 0:
            # Smoothly update ambient noise floor towards non-speech energy level
            if self.ambient_noise_floor <= 0:
                self.ambient_noise_floor = rms
            else:
                self.ambient_noise_floor = (self.ambient_noise_floor * 0.85) + (rms * 0.15)
            # Speech trigger threshold is at least 1.8x ambient noise floor, clamped between min and max
            computed = max(self.ambient_noise_floor * 1.8, self.min_energy_threshold)
            self.adaptive_threshold = min(computed, self.max_energy_threshold)

    def _run_loop(self) -> None:
        """Main 12-state state machine loop."""
        logger.info("WakeWordEngine thread loop running...")
        standby_chunk = os.path.join(self.temp_dir, "standby_chunk.wav")

        while self._is_running and not self._stop_event.is_set():
            # Check for cross-process control directives (mute, unmute, stop, barge_in, push_to_talk)
            self._check_daemon_commands()
            if not self._is_running or self._stop_event.is_set():
                break

            # Acoustic Feedback Guard: Suppress VAD while TTS is actively playing through physical speaker
            if self._is_tts_playing():
                self._stop_event.wait(0.2)
                continue

            curr = self.state

            if curr == WakeState.MUTED:
                self._stop_event.wait(0.5)
                continue

            elif curr == WakeState.STANDBY_LISTENING:
                if not self.wake_word_enabled:
                    self._stop_event.wait(0.2)
                    continue
                # 1. Capture small 1.5-second audio window
                ok = self._record_audio_chunk(standby_chunk, duration_s=1.5)
                if not ok:
                    self._prev_standby_frames = None
                    self._stop_event.wait(self._get_recorder_backoff_delay())
                    continue

                # 2. Check energy against adaptive threshold
                rms = self._calculate_audio_rms(standby_chunk)
                if rms > self.adaptive_threshold:
                    matched = False
                    # A. Local Acoustic Neural Wake-Word Detection (openWakeWord)
                    acoustic_score = self._score_acoustic_wake(standby_chunk)
                    if acoustic_score >= self._wake_threshold:
                        logger.info(">>> ACOUSTIC WAKE WORD DETECTED! (score: %.3f >= threshold: %.2f) <<<",
                                    acoustic_score, self._wake_threshold)
                        self._current_transcript = ""
                        self._prev_standby_frames = None
                        self.set_state(WakeState.WAKE_DETECTED)
                        continue

                    # B. Check rolling boundary chunk if previous audio contained energy
                    if self._prev_standby_frames is not None:
                        combined_path = os.path.join(self.temp_dir, "standby_combined.wav")
                        try:
                            with wave.open(standby_chunk, "rb") as wf:
                                current_frames = wf.readframes(wf.getnframes())
                                current_params = wf.getparams()
                            with wave.open(combined_path, "wb") as wf:
                                wf.setparams(current_params)
                                wf.writeframes(self._prev_standby_frames + current_frames)
                            combined_score = self._score_acoustic_wake(combined_path)
                            if combined_score >= self._wake_threshold:
                                logger.info(">>> ACOUSTIC WAKE WORD DETECTED (across boundary, score: %.3f)! <<<",
                                            combined_score)
                                self._current_transcript = ""
                                self._prev_standby_frames = None
                                self.set_state(WakeState.WAKE_DETECTED)
                                continue
                        except Exception as ex:
                            logger.debug("Error checking rolling acoustic chunk: %s", ex)

                    # C. Fallback: Secondary STT regex match for noisy environments or compound phrases
                    text = self._transcribe(standby_chunk)
                    if text:
                        logger.debug("Speech detected in standby (RMS: %.1f, threshold: %.1f): '%s'", rms, self.adaptive_threshold, text)
                        if self._matches_wake_phrase(text):
                            logger.info(">>> WAKE PHRASE DETECTED VIA STT MATCH! <<<")
                            self._current_transcript = self._command_after_wake_phrase(text)
                            self._prev_standby_frames = None
                            self.set_state(WakeState.LISTENING_SPEECH if self._current_transcript else WakeState.WAKE_DETECTED)
                            matched = True
                            continue

                    if not matched:
                        # Non-speech / ambient noise chunk
                        self._prev_standby_frames = None
                        self._update_adaptive_threshold(rms, is_speech=False)
                    else:
                        try:
                            with wave.open(standby_chunk, "rb") as wf:
                                self._prev_standby_frames = wf.readframes(wf.getnframes())
                        except Exception:
                            self._prev_standby_frames = None
                else:
                    self._prev_standby_frames = None
                    self._update_adaptive_threshold(rms, is_speech=False)

                self._stop_event.wait(0.05)

            elif curr == WakeState.FOLLOW_UP_STANDBY:
                # User has 15 seconds to speak a follow-up command without repeating wake word
                now = time.time()
                if now > self._follow_up_deadline:
                    logger.info("Follow-up conversation window expired. Returning to STANDBY_LISTENING.")
                    self.set_state(WakeState.STANDBY_LISTENING)
                    continue

                # Capture short window to detect follow-up speech
                ok = self._record_audio_chunk(standby_chunk, duration_s=1.5)
                if ok:
                    rms = self._calculate_audio_rms(standby_chunk)
                    if rms > self.adaptive_threshold:
                        text = self._transcribe(standby_chunk)
                        if text and len(text.split()) >= 1:
                            logger.debug("Direct follow-up speech detected: %s", text)
                            self._current_transcript = text
                            self.set_state(WakeState.LISTENING_SPEECH)
                            continue
                    else:
                        self._update_adaptive_threshold(rms, is_speech=False)
                self._stop_event.wait(0.05)

            elif curr == WakeState.WAKE_DETECTED:
                # Immediate acknowledgment speech
                try:
                    from apps.voice.service import voice_service
                    voice_service.stop_playback()
                    from apps.voice.tts import TextToSpeech
                    tts = TextToSpeech(simulation_mode=False)
                    tts.speak_sync("Yes, I'm listening.")
                except Exception as ex:
                    logger.debug("Wake acknowledgment notice: %s", ex)

                self._current_transcript = ""
                self._last_speech_time = time.time()
                self.set_state(WakeState.LISTENING_SPEECH)

            elif curr == WakeState.LISTENING_SPEECH:
                # Capture rolling speech chunks until 3.0s continuous silence
                cmd_parts: List[str] = []
                accumulated_frames: List[bytes] = []
                accumulated_bytes = 0
                audio_params = None
                if self._current_transcript:
                    cmd_parts.append(self._current_transcript)

                speech_chunk = os.path.join(self.temp_dir, "speech_chunk.wav")
                self._last_speech_time = time.time()
                has_heard_speech = bool(cmd_parts)

                while self._is_running and not self._stop_event.is_set():
                    self._check_daemon_commands()
                    if self.state not in {WakeState.LISTENING_SPEECH, WakeState.STREAMING_TRANSCRIPTION, WakeState.SILENCE_COUNTDOWN}:
                        break
                    # Acoustic Feedback Guard inside listening loop
                    if self._is_tts_playing():
                        self._stop_event.wait(0.2)
                        continue

                    ok = self._record_audio_chunk(speech_chunk, duration_s=1.5)
                    if not ok:
                        self._stop_event.wait(self._get_recorder_backoff_delay())
                        continue

                    rms = self._calculate_audio_rms(speech_chunk)

                    # Read raw frames to accumulate full utterance
                    try:
                        with wave.open(speech_chunk, "rb") as wf:
                            audio_params = wf.getparams()
                            frames = wf.readframes(wf.getnframes())
                            if rms > self.adaptive_threshold or has_heard_speech:
                                accumulated_bytes += len(frames)
                                if accumulated_bytes > 1_920_000:
                                    self._current_transcript = ""
                                    self._last_error = "Voice request exceeded the capture limit; no command was submitted."
                                    self.set_state(WakeState.STANDBY_LISTENING)
                                    break
                                accumulated_frames.append(frames)
                    except Exception as ex:
                        logger.debug("Error reading speech chunk frames: %s", ex)

                    if rms > self.adaptive_threshold:
                        # User spoke in this window
                        has_heard_speech = True
                        self._last_speech_time = time.time()
                        self.set_state(WakeState.STREAMING_TRANSCRIPTION)

                        text_chunk = self._transcribe(speech_chunk)
                        # Recognition time is a capture gap, not observed silence.
                        self._last_speech_time = time.time()
                        if text_chunk:
                            cmd_parts.append(text_chunk)
                            self._current_transcript = " ".join(cmd_parts)
                            logger.debug("Speech chunk transcribed")

                        self.set_state(WakeState.LISTENING_SPEECH)
                    else:
                        # Silence in this window
                        elapsed_silence = time.time() - self._last_speech_time
                        if has_heard_speech:
                            self.set_state(WakeState.SILENCE_COUNTDOWN)
                            logger.info("Silence countdown: %.1fs / %.1fs", elapsed_silence, self.silence_timeout_s)
                            if elapsed_silence >= self.silence_timeout_s:
                                logger.info("3.0s continuous silence reached! Finalizing command.")
                                self.set_state(WakeState.COMMAND_SUBMITTED)
                                break
                        elif elapsed_silence >= (self.silence_timeout_s * 2):
                            # User didn't say anything after wake word
                            logger.info("No speech detected after wake word. Returning to standby.")
                            self.set_state(WakeState.STANDBY_LISTENING)
                            break

                if self.state == WakeState.COMMAND_SUBMITTED:
                    final_cmd = self._current_transcript.strip()
                    # Use only this turn's audio; old recordings can never supply
                    # a command after a capture failure or interruption.
                    if not final_cmd and accumulated_frames and audio_params:
                        try:
                            with tempfile.NamedTemporaryFile(prefix="accumulated_command_", suffix=".wav", dir=self.temp_dir) as captured:
                                with wave.open(captured.name, "wb") as wf:
                                    wf.setparams(audio_params)
                                    wf.writeframes(b"".join(accumulated_frames))
                                full_transcript = self._transcribe(captured.name)
                                if full_transcript and full_transcript.strip():
                                    final_cmd = full_transcript.strip()
                                    self._current_transcript = final_cmd
                        except Exception as e:
                            logger.debug("Accumulated transcription unavailable (%s)", type(e).__name__)

                    self._last_command = final_cmd
                    if final_cmd:
                        logger.info("Submitting recognized voice command")
                        self.set_state(WakeState.PROCESSING_AGENT)
                        self._execute_command_and_respond(final_cmd)
                    else:
                        logger.info("No speech recognized in command utterance; returning to standby.")
                        self.set_state(WakeState.STANDBY_LISTENING)

    def _execute_command_and_respond(self, command_text: str) -> None:
        """Route recognized command to JARVIS Brain, deliver dual text/speech, and enter follow-up window."""
        try:
            submitted_to_backend = False
            self._last_error = None
            self._last_response = ""

            # 1. Let the authoritative backend refresh its own identity session.
            # The daemon is a separate process, so forwarding its in-memory
            # session would be both stale and unsafe. A failed recognition is
            # intentionally non-fatal: the backend retains or falls back to a
            # GUEST session.
            try:
                identity = requests.post(
                    "http://127.0.0.1:8000/api/voice/session/identify",
                    timeout=8.0,
                )
                if identity.status_code != 200:
                    logger.warning("Voice identity refresh was rejected (HTTP %s); using safe existing session.", identity.status_code)
            except Exception as e:
                logger.debug("Voice identity refresh unavailable (%s); using safe existing session.", e)

            # 2. Submit only the transcript. The backend resolves the session
            # from its own trusted state and rejects caller-supplied roles.
            try:
                resp = requests.post(
                    "http://127.0.0.1:8000/api/voice/command",
                    json={"text": command_text},
                    timeout=95.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data.get("response") if isinstance(data, dict) else None
                    if not isinstance(response_text, str) or not response_text.strip():
                        raise ValueError("Backend returned no command result")
                    self._last_response = response_text
                    submitted_to_backend = True
            except Exception as e:
                logger.warning("Voice command outcome is unknown (%s); it will not be replayed.", type(e).__name__)

            if not submitted_to_backend:
                # The backend may already have executed an action before a timeout,
                # disconnect, or invalid response. Retrying here could execute it twice.
                self._last_error = "Command completion could not be verified. Check the dashboard before retrying."
                self._last_response = self._last_error
                self._follow_up_deadline = 0.0
                self.set_state(WakeState.STANDBY_LISTENING)
                return

            # 2. Enter 15-second follow-up window
            self._follow_up_deadline = time.time() + self.follow_up_window_s
            self.set_state(WakeState.FOLLOW_UP_STANDBY)
            logger.info("Entered 15-second follow-up window until %.1f", self._follow_up_deadline)

        except Exception as exc:
            logger.error("Command processing error: %s", exc)
            self._last_error = str(exc)
            self.set_state(WakeState.ERROR)
            time.sleep(2.0)
            self.set_state(WakeState.STANDBY_LISTENING)


# Module-level singleton
wake_word_engine = WakeWordEngine()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [JARVIS-VOICE-SERVICE] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger.info("Initializing JARVIS Background Voice & Wake-Word Service...")
    wake_word_engine.run_forever()
