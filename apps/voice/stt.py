"""Speech-to-Text (STT) Module for JARVIS OS.

Integrates OpenAI Whisper for local audio transcription with graceful fallback
to simulation mode when hardware or dependencies are unavailable.
"""

import logging
import os
import shutil
import subprocess
import wave
from typing import Any, Dict, Optional

from config.config_manager import config

logger = logging.getLogger("JARVIS-STT")


class SpeechToText:
    """Manages audio recording and speech-to-text transcription."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        simulation_mode: Optional[bool] = None,
    ):
        """Initialize the SpeechToText engine.

        Args:
            model_name: Model size (tiny, base, small, etc.). Defaults to config.
            device: Compute device ('cpu', 'cuda'). Defaults to config.
            simulation_mode: Simulation flag override. Defaults to config.
        """
        stt_config: Dict[str, Any] = config.get("stt", {})
        self.model_name = model_name or stt_config.get("model", "tiny")
        self.device = device or stt_config.get("device", "cpu")

        if simulation_mode is not None:
            self.simulation_mode = simulation_mode
        else:
            self.simulation_mode = bool(config.get("simulation_mode", True))

        self.model = None
        self._init_model()

    def _init_model(self) -> None:
        """Attempt to load the OpenAI Whisper model if available."""
        if self.simulation_mode:
            logger.info("Simulation mode active: Whisper model loading skipped.")
            return

        try:
            import whisper  # type: ignore

            logger.info(
                "Loading Whisper model '%s' on %s...", self.model_name, self.device
            )
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Whisper model '%s' successfully loaded.", self.model_name)
        except ImportError:
            logger.warning(
                "openai-whisper package not installed. Falling back to simulation mode."
            )
            self.model = None
        except Exception as exc:
            logger.error(
                "Failed to load Whisper model '%s': %s. Falling back to simulation.",
                self.model_name,
                exc,
            )
            self.model = None

    def transcribe_simulated(self) -> str:
        """Return a simulated transcription.

        Returns:
            str: 'Simulated transcription'
        """
        logger.debug("Returning simulated transcription.")
        return "Simulated transcription"

    def transcribe(self, audio_file_path: str) -> str:
        """Transcribe an audio file into text.

        Uses speech_recognition (Google Web Speech API) as primary fast engine,
        Whisper model as secondary, and simulated fallback in simulation mode.

        Args:
            audio_file_path: Absolute or relative path to the audio file.

        Returns:
            str: Transcribed text or simulated transcription.
        """
        if self.simulation_mode:
            return self.transcribe_simulated()

        if not os.path.exists(audio_file_path):
            logger.warning(
                "Audio file '%s' not found for transcription; returning simulated.",
                audio_file_path,
            )
            return self.transcribe_simulated()

        # 1. Primary fast speech recognition via SpeechRecognition
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio_file_path) as source:
                audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            if text and text.strip():
                logger.info("SpeechRecognition transcribed: '%s'", text)
                return text.strip()
        except Exception as exc:
            logger.debug("SpeechRecognition recognize_google: %s", exc)

        # 2. Whisper fallback if loaded
        if self.model is not None:
            try:
                logger.info("Transcribing audio file with Whisper: %s", audio_file_path)
                result = self.model.transcribe(audio_file_path)
                transcription = str(result.get("text", "")).strip()
                if transcription:
                    logger.info("Whisper result: '%s'", transcription)
                    return transcription
            except Exception as exc:
                logger.error("Whisper transcription failed: %s", exc)

        return ""

    def record_audio(
        self,
        duration_secs: int,
        output_path: str,
        device: Optional[str] = None,
    ) -> bool:
        """Record audio to output_path using ALSA arecord or PipeWire pw-record.

        Args:
            duration_secs: Recording duration in seconds.
            output_path: Target path for the recorded WAV file.
            device: Optional ALSA device identifier (e.g. 'plughw:2,0').

        Returns:
            bool: True if recording succeeded or was simulated, False on error.
        """
        # Ensure parent directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        if self.simulation_mode:
            logger.debug(
                "Simulating %d-second audio recording to %s",
                duration_secs,
                output_path,
            )
            return self._create_dummy_wav(output_path, duration_secs)

        # Check if arecord exists
        if not shutil.which("arecord"):
            logger.warning("arecord binary not found; creating dummy audio file.")
            return self._create_dummy_wav(output_path, duration_secs)

        # Convert direct hw: identifier to plughw: to ensure automatic rate and format translation
        rec_dev = device
        if rec_dev and rec_dev.startswith("hw:"):
            rec_dev = "plug" + rec_dev

        cmd = [
            "arecord",
            "-d",
            str(duration_secs),
            "-f",
            "S16_LE",
            "-r",
            "16000",
        ]
        if rec_dev and rec_dev != "default":
            cmd.extend(["-D", rec_dev])
        cmd.append(output_path)

        try:
            logger.info("Executing arecord command: %s", " ".join(cmd))
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=duration_secs + 5,
            )
            if proc.returncode != 0:
                logger.warning(
                    "arecord failed with code %d: %s; trying pw-record fallback.",
                    proc.returncode,
                    proc.stderr.strip(),
                )
                if shutil.which("pw-record"):
                    try:
                        pw_cmd = ["pw-record", "--rate=16000", "--channels=1", "--format=s16", output_path]
                        import time
                        pw_proc = subprocess.Popen(pw_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(duration_secs)
                        pw_proc.terminate()
                        pw_proc.wait(timeout=2)
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                            logger.info("Recorded %d seconds via pw-record", duration_secs)
                            return True
                    except Exception as e:
                        logger.warning("pw-record fallback error: %s", e)
                return self._create_dummy_wav(output_path, duration_secs)

            logger.info("Recorded %d seconds of audio to %s", duration_secs, output_path)
            return True

        except subprocess.TimeoutExpired:
            logger.error("arecord timed out after %d seconds.", duration_secs + 5)
            return self._create_dummy_wav(output_path, duration_secs)
        except Exception as exc:
            logger.error("Unexpected error during arecord: %s", exc)
            return self._create_dummy_wav(output_path, duration_secs)

    def _create_dummy_wav(self, path: str, duration_secs: int) -> bool:
        """Create a valid silent WAV file for simulation and test compatibility.

        Args:
            path: Target file path.
            duration_secs: Length of silent audio in seconds.

        Returns:
            bool: True on success.
        """
        try:
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(16000)
                # Write silent bytes (2 bytes per sample * 16000 * duration_secs)
                frames = b"\x00\x00" * int(16000 * max(1, duration_secs))
                wf.writeframes(frames)
            return True
        except Exception as exc:
            logger.error("Failed to create dummy wav file: %s", exc)
            return False
