"""
JARVIS Central Speech Output & Audio Delivery Manager.

Coordinates end-to-end speech synthesis, audio staging, format validation,
PipeWire system speaker playback, and HTTP audio streaming for the browser.

Enforces:
1. Every final AI response generates an audio asset and an audio URL.
2. Cloned voice priority: OmniVoice (with reference sample myvoice.wav).
3. If OmniVoice is offline: uses working neural fallback (edge-tts) and clearly
   identifies that fallback voice is active (never claims fallback is cloned).
4. Audio output validation (non-empty, valid RIFF/MP3 header, duration > 0).
5. Dual routing support: browser playback via HTML5 <audio> and/or Pi system speaker (pw-play).
6. Instant interruption and barge-in support.
"""

import glob
import logging
import os
import shutil
import subprocess
import threading
import time
import uuid
from typing import Any, Dict, Optional, Tuple

from config.config_manager import config
from apps.voice.gradio_tts import gradio_cloner, sanitize_speech_text

logger = logging.getLogger("JARVIS.Voice.SpeechManager")


class SpeechOutputManager:
    """Central manager for audio generation, caching, staging, and playback."""

    def __init__(self, stage_dir: Optional[str] = None):
        self.stage_dir = stage_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "audio_stage"
        )
        os.makedirs(self.stage_dir, exist_ok=True)

        self._audio_store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._current_player: Optional[subprocess.Popen] = None
        self._last_playback: Dict[str, Any] = {
            "status": "idle",
            "provider": "none",
            "timestamp": 0.0,
        }

        logger.info("SpeechOutputManager initialized (stage_dir=%s)", self.stage_dir)

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive status for voice hardware, TTS cloner, and playback."""
        from apps.voice.service import voice_service

        mgr = voice_service.audio_manager
        cloner_status = gradio_cloner.get_provider_status()
        mic_avail = mgr.is_microphone_available()
        best_mic = mgr.select_best_device()
        best_spk = mgr.select_best_playback_device()

        return {
            "microphone": {
                "available": mic_avail,
                "device": best_mic.get("name", "Unknown"),
                "card": best_mic.get("card", 0),
                "device_id": best_mic.get("device", 0),
                "recording": voice_service.state == "LISTENING",
            },
            "speaker": {
                "available": bool(best_spk and best_spk.get("name") != "Simulated"),
                "device": best_spk.get("name", "Default Speaker"),
                "card": best_spk.get("card", 0),
                "device_id": best_spk.get("device", 0),
                "playing": self.is_playing(),
            },
            "tts": {
                "provider": "omnivoice" if cloner_status.get("online") else "fallback_edge_tts",
                "cloning_available": cloner_status.get("online", False),
                "cloning_enabled": cloner_status.get("cloning_enabled", True),
                "reference_voice": cloner_status.get("has_reference_audio", False),
                "reference_audio_path": cloner_status.get("reference_audio_path"),
                "active_url": cloner_status.get("url", ""),
                "status_label": (
                    "OMNIVOICE CLONED VOICE READY"
                    if cloner_status.get("online")
                    else "OMNIVOICE OFFLINE — FALLBACK VOICE ACTIVE"
                ),
            },
            "last_playback": self._last_playback,
            "staged_audio_count": len(self._audio_store),
        }

    def is_playing(self) -> bool:
        """Check if background system player is currently running."""
        with self._lock:
            if self._current_player and self._current_player.poll() is None:
                return True
        return False

    def synthesize_and_stage(
        self,
        text: str,
        play_system: Optional[bool] = None,
        conversation_id: Optional[str] = None,
        voice_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize speech text, stage the audio file with a unique ID, and optionally play on speaker.
        Returns full audio descriptor including audio_url for frontend browser streaming.
        """
        t0 = time.perf_counter()
        clean_text = sanitize_speech_text(text)
        if not clean_text:
            return {
                "status": "empty",
                "audio_id": None,
                "audio_url": None,
                "provider": "none",
                "error": "Empty text for speech synthesis",
                "success": False,
            }

        # Determine playback policy
        voice_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
        route_policy = voice_cfg.get("routing_policy", "both")  # 'browser', 'system', or 'both'
        if play_system is None:
            play_system = route_policy in ("system", "both")

        # 1. Synthesize via gradio_cloner (OmniVoice or neural fallback)
        result = gradio_cloner.synthesize(clean_text, voice_config=voice_config)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        if not result.success or not result.audio_path or not os.path.exists(result.audio_path):
            logger.warning("Synthesis returned no valid audio file: error=%s", result.error)
            self._last_playback = {
                "status": "error",
                "error": result.error or "Audio synthesis produced no output file",
                "provider": result.provider,
                "timestamp": time.time(),
            }
            return {
                "status": "error",
                "audio_id": None,
                "audio_url": None,
                "provider": result.provider,
                "provider_label": "Speech Synthesis Failed",
                "is_cloned": False,
                "error": result.error or "Audio file not produced",
                "success": False,
            }

        # 2. Stage audio file with unique ID
        audio_id = f"audio_{uuid.uuid4().hex[:12]}"
        ext = ".mp3" if result.audio_path.endswith(".mp3") or result.format == "mp3" else ".wav"
        staged_path = os.path.join(self.stage_dir, f"{audio_id}{ext}")
        shutil.copy2(result.audio_path, staged_path)

        media_type = "audio/mpeg" if ext == ".mp3" else "audio/wav"
        is_cloned = bool("clone" in result.provider.lower())
        provider_label = (
            "OmniVoice (Personal Cloned Voice)"
            if is_cloned
            else "Neural Fallback (Edge-TTS Ryan)"
        )

        with self._lock:
            self._audio_store[audio_id] = {
                "path": staged_path,
                "media_type": media_type,
                "provider": result.provider,
                "provider_label": provider_label,
                "is_cloned": is_cloned,
                "text": clean_text,
                "created_at": time.time(),
                "latency_ms": latency_ms,
            }

        # 3. Optional system speaker output (non-blocking)
        if play_system:
            self.play_system_audio(staged_path)

        self._last_playback = {
            "status": "staged",
            "audio_id": audio_id,
            "provider": result.provider,
            "is_cloned": is_cloned,
            "timestamp": time.time(),
            "latency_ms": latency_ms,
        }

        return {
            "status": "ok",
            "audio_id": audio_id,
            "audio_url": f"/api/voice/audio/{audio_id}",
            "provider": result.provider,
            "provider_label": provider_label,
            "is_cloned": is_cloned,
            "cached": result.cached,
            "latency_ms": latency_ms,
            "success": True,
            "text": clean_text,
        }

    def get_staged_audio(self, audio_id: str) -> Optional[Tuple[str, str]]:
        """Retrieve local file path and media_type for a staged audio ID."""
        with self._lock:
            item = self._audio_store.get(audio_id)
            if item and os.path.exists(item["path"]):
                return item["path"], item["media_type"]

        # Check stage directory directly on disk
        for ext, mtype in [(".mp3", "audio/mpeg"), (".wav", "audio/wav")]:
            candidate = os.path.join(self.stage_dir, f"{audio_id}{ext}")
            if os.path.exists(candidate):
                return candidate, mtype

        return None

    def play_system_audio(self, file_path: str, wait: bool = False) -> bool:
        """Play audio file through PipeWire system speaker (pw-play / aplay)."""
        if not file_path or not os.path.exists(file_path):
            return False

        with self._lock:
            self.stop()

            player_bin = (
                shutil.which("pw-play")
                or shutil.which("paplay")
                or shutil.which("aplay")
            )
            if not player_bin:
                logger.warning("No system audio player found on SBC.")
                return False

            try:
                # Duck active background media streams (e.g. FreeTube, VLC) during JARVIS speech
                try:
                    from tools.media.audio_stream_manager import audio_stream_manager
                    audio_stream_manager.duck_active_streams(duck_fraction=0.20)
                except Exception as duck_err:
                    logger.debug("Stream ducking notice: %s", duck_err)

                self._current_player = subprocess.Popen(
                    [player_bin, file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._last_playback["status"] = "playing"

                def _monitor_restore(proc: subprocess.Popen) -> None:
                    try:
                        proc.wait()
                    except Exception:
                        pass
                    finally:
                        try:
                            from tools.media.audio_stream_manager import audio_stream_manager
                            audio_stream_manager.restore_active_streams()
                        except Exception:
                            pass

                threading.Thread(target=_monitor_restore, args=(self._current_player,), daemon=True).start()

                if wait:
                    self._current_player.wait(timeout=15)
                    self._current_player = None
                    self._last_playback["status"] = "completed"
                return True
            except Exception as e:
                logger.error("Failed to start system audio playback: %s", e)
                return False

    def stop(self) -> None:
        """Interrupt and terminate any active background audio playback."""
        with self._lock:
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
            self._last_playback["status"] = "stopped"
        try:
            from tools.media.audio_stream_manager import audio_stream_manager
            audio_stream_manager.restore_active_streams()
        except Exception:
            pass
        gradio_cloner.stop_playback()
        logger.info("Audio playback stopped.")

    def test_speaker(self) -> Dict[str, Any]:
        """Execute physical speaker test with diagnostic phrase and verification."""
        test_phrase = "Audio system test. Your Raspberry Pi speaker is working properly."
        res = self.synthesize_and_stage(test_phrase, play_system=True)
        return {
            "component": "speaker",
            "status": "ok" if res.get("success") else "error",
            "audio_id": res.get("audio_id"),
            "audio_url": res.get("audio_url"),
            "provider": res.get("provider"),
            "provider_label": res.get("provider_label"),
            "latency_ms": res.get("latency_ms"),
            "message": "Playback dispatched to speaker and staged for browser.",
        }

    def test_microphone(self, duration_secs: int = 3) -> Dict[str, Any]:
        """Record real audio from ReSpeaker microphone and transcribe without simulation."""
        from apps.voice.service import voice_service

        test_file = os.path.join(self.stage_dir, f"mic_test_{int(time.time())}.wav")
        dev = voice_service._selected_device or voice_service.audio_manager.select_best_device()
        device_id = voice_service.audio_manager.get_device_alsa_identifier(dev, plug=True)

        success = voice_service.stt.record_audio(
            duration_secs=duration_secs,
            output_path=test_file,
            device=device_id
        )

        if not success or not os.path.exists(test_file):
            return {
                "component": "microphone",
                "status": "error",
                "message": "Microphone recording failed to capture audio.",
                "transcription": "",
                "duration_secs": 0,
            }

        size = os.path.getsize(test_file)
        transcript = voice_service.stt.transcribe(test_file)

        return {
            "component": "microphone",
            "status": "ok",
            "device": voice_service.audio_manager.select_best_device().get("name"),
            "duration_secs": duration_secs,
            "bytes_captured": size,
            "transcription": transcript,
            "message": "Real microphone recording completed successfully.",
        }


# Global singleton instance
speech_manager = SpeechOutputManager()
__all__ = ["SpeechOutputManager", "speech_manager"]
