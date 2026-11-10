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
    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-active", "jarvis-voice.service"],
            capture_output=True,
            text=True,
            check=False,
            timeout=1.5,
        )
        return res.stdout.strip() == "active"
    except Exception:
        return False


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
        self.ambient_noise_floor: float = 40.0
        self.adaptive_threshold: float = float(v_cfg.get("energy_threshold", energy_threshold))
        self.min_energy_threshold: float = 90.0
        self.max_energy_threshold: float = 350.0

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

    def set_command_handler(self, handler: Callable[[str], Any]) -> None:
        self._on_command_handler = handler

    def get_status(self) -> Dict[str, Any]:
        """Return full telemetry dictionary for the dashboard status indicator."""
        with self._state_lock:
            now = time.time()
            elapsed_in_state = round(now - self._state_entered_time, 2)
            follow_up_remaining = max(0.0, round(self._follow_up_deadline - now, 1)) if self._state == WakeState.FOLLOW_UP_STANDBY else 0.0

            return {
                "state": self._state.value,
                "is_running": self._is_running,
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

        self._run_loop()

    def stop(self) -> None:
        """Stop the background voice assistant."""
        with self._state_lock:
            self._is_running = False
            self._stop_event.set()
            self.set_state(WakeState.DISABLED)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("WakeWordEngine stopped.")

    def mute(self) -> None:
        """Temporarily mute listening."""
        self.set_state(WakeState.MUTED)

    def unmute(self) -> None:
        """Unmute listening back to standby."""
        self.set_state(WakeState.STANDBY_LISTENING)

    def _calculate_audio_rms(self, wav_path: str) -> float:
        """Calculate Root Mean Square audio amplitude for voice energy detection."""
        if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
            return 0.0
        try:
            with wave.open(wav_path, "rb") as wf:
                n_frames = wf.getnframes()
                if n_frames == 0:
                    return 0.0
                raw_bytes = wf.readframes(n_frames)
                fmt = f"{n_frames}h"
                samples = struct.unpack(fmt, raw_bytes)
                sum_sq = sum(s * s for s in samples)
                return math.sqrt(sum_sq / max(1, len(samples)))
        except Exception as e:
            logger.debug("RMS calculation error on %s: %s", wav_path, e)
            return 0.0

    def _record_audio_chunk(self, output_path: str, duration_s: float = 1.5) -> bool:
        """Record audio chunk using pw-record with PipeWire default source."""
        try:
            cmd = ["pw-record", "--rate=16000", "--channels=1", "--format=s16", output_path]
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(duration_s)
            proc.terminate()
            try:
                proc.communicate(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()

            return os.path.exists(output_path) and os.path.getsize(output_path) > 300
        except Exception as e:
            logger.error("Audio recording error: %s", e)
            return False

    def _transcribe(self, wav_path: str) -> str:
        """Transcribe an audio chunk using real speech recognition without mock data."""
        try:
            if self.stt:
                text = self.stt.transcribe(wav_path)
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

    def _is_tts_playing(self) -> bool:
        """Check if JARVIS physical speaker is currently outputting speech (prevents acoustic feedback)."""
        try:
            from apps.voice.speech_manager import speech_manager
            return speech_manager.is_playing()
        except Exception:
            return False

    def _update_adaptive_threshold(self, rms: float) -> None:
        """Smoothly calibrate noise floor and compute dynamic energy threshold."""
        if rms < self.adaptive_threshold:
            # Smoothly update ambient noise floor
            self.ambient_noise_floor = (self.ambient_noise_floor * 0.85) + (rms * 0.15)
            # Threshold is at least 2.0x noise floor, clamped between min and max
            computed = max(self.ambient_noise_floor * 2.0, self.min_energy_threshold)
            self.adaptive_threshold = min(computed, self.max_energy_threshold)

    def _run_loop(self) -> None:
        """Main 12-state state machine loop."""
        logger.info("WakeWordEngine thread loop running...")
        standby_chunk = os.path.join(self.temp_dir, "standby_chunk.wav")

        while self._is_running and not self._stop_event.is_set():
            # Acoustic Feedback Guard: Suppress VAD while TTS is actively playing through physical speaker
            if self._is_tts_playing():
                self._stop_event.wait(0.2)
                continue

            curr = self.state

            if curr == WakeState.MUTED:
                self._stop_event.wait(0.5)
                continue

            elif curr == WakeState.STANDBY_LISTENING:
                # 1. Capture small 1.5-second audio window
                ok = self._record_audio_chunk(standby_chunk, duration_s=1.5)
                if not ok:
                    self._stop_event.wait(0.2)
                    continue

                # 2. Check energy against adaptive threshold
                rms = self._calculate_audio_rms(standby_chunk)
                if rms > self.adaptive_threshold:
                    # Potential speech detected, transcribe
                    text = self._transcribe(standby_chunk)
                    if text:
                        logger.info("Heard in standby: '%s' (RMS: %.1f, threshold: %.1f)", text, rms, self.adaptive_threshold)
                        if self._matches_wake_phrase(text):
                            logger.info(">>> WAKE PHRASE DETECTED! <<<")
                            self.set_state(WakeState.WAKE_DETECTED)
                            continue
                else:
                    self._update_adaptive_threshold(rms)

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
                            logger.info("Direct follow-up command heard: '%s'", text)
                            self._current_transcript = text
                            self.set_state(WakeState.LISTENING_SPEECH)
                            continue
                    else:
                        self._update_adaptive_threshold(rms)
                self._stop_event.wait(0.05)

            elif curr == WakeState.WAKE_DETECTED:
                # Immediate acknowledgment chime/speech
                try:
                    from apps.voice.service import voice_service
                    voice_service.stop_playback()
                    from apps.voice.tts import TextToSpeech
                    tts = TextToSpeech(simulation_mode=False)
                    tts.speak_sync("Yes?")
                except Exception as ex:
                    logger.debug("Wake acknowledgment notice: %s", ex)

                self._current_transcript = ""
                self._last_speech_time = time.time()
                self.set_state(WakeState.LISTENING_SPEECH)

            elif curr == WakeState.LISTENING_SPEECH:
                # Capture rolling speech chunks until 3.0s continuous silence
                cmd_parts: List[str] = []
                if self._current_transcript:
                    cmd_parts.append(self._current_transcript)

                speech_chunk = os.path.join(self.temp_dir, "speech_chunk.wav")
                self._last_speech_time = time.time()
                has_heard_speech = bool(cmd_parts)

                while self._is_running and not self._stop_event.is_set():
                    # Acoustic Feedback Guard inside listening loop
                    if self._is_tts_playing():
                        self._stop_event.wait(0.2)
                        continue

                    ok = self._record_audio_chunk(speech_chunk, duration_s=1.5)
                    if not ok:
                        continue

                    rms = self._calculate_audio_rms(speech_chunk)

                    if rms > self.adaptive_threshold:
                        # User spoke in this window
                        has_heard_speech = True
                        self._last_speech_time = time.time()
                        self.set_state(WakeState.STREAMING_TRANSCRIPTION)

                        text_chunk = self._transcribe(speech_chunk)
                        if text_chunk:
                            cmd_parts.append(text_chunk)
                            self._current_transcript = " ".join(cmd_parts)
                            logger.info("Live speech stream: '%s'", self._current_transcript)

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
                    self._last_command = final_cmd
                    if final_cmd:
                        logger.info("Executing automatic submitted command: '%s'", final_cmd)
                        self.set_state(WakeState.PROCESSING_AGENT)
                        self._execute_command_and_respond(final_cmd)
                    else:
                        self.set_state(WakeState.STANDBY_LISTENING)

    def _execute_command_and_respond(self, command_text: str) -> None:
        """Route recognized command to JARVIS Brain, deliver dual text/speech, and enter follow-up window."""
        try:
            submitted_to_backend = False
            # 1. Try sending command via localhost REST API to trigger coordinated UI updates and audio
            try:
                resp = requests.post(
                    "http://127.0.0.1:8000/api/voice/command",
                    json={"text": command_text},
                    timeout=20.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self._last_response = data.get("response", "")
                    submitted_to_backend = True
            except Exception as e:
                logger.debug("REST command dispatch failed or backend offline (%s); falling back to direct execution.", e)

            if not submitted_to_backend:
                # Fallback: direct in-process execution
                try:
                    from apps.api.websocket_api import broadcast_chat_message
                    broadcast_chat_message(role="user", text=command_text)
                except Exception as e:
                    logger.debug("Failed to broadcast user chat message: %s", e)

                if self._on_command_handler:
                    response = self._on_command_handler(command_text)
                else:
                    from ai.brain import get_brain
                    brain = get_brain()
                    chat_res = brain.chat(command_text, session_id="voice-session")
                    response = chat_res.get("response", "Command executed.")

                self._last_response = str(response)

                try:
                    from apps.api.websocket_api import broadcast_chat_message
                    broadcast_chat_message(role="assistant", text=self._last_response)
                except Exception as e:
                    logger.debug("Failed to broadcast assistant chat message: %s", e)

                self.set_state(WakeState.SPEAKING_RESPONSE)
                from apps.voice.speech_manager import speech_manager
                speech_manager.synthesize_and_stage(str(response), play_system=True)

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
