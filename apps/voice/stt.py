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
        self.language = stt_config.get("language", "en-US")
        self.supported_languages = ["en-US", "hi-IN", "ne-NP"]

        if simulation_mode is not None:
            self.simulation_mode = simulation_mode
        else:
            voice_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
            if "simulation_mode" in voice_cfg:
                self.simulation_mode = bool(voice_cfg["simulation_mode"])
            else:
                self.simulation_mode = False

        self.model = None
        self.last_status = "idle"
        # Loading even Whisper's tiny model can take tens of seconds and may
        # download weights.  Keep API/server startup responsive and load it
        # only after the lightweight STT provider is unavailable for a real
        # transcription request.
        self._model_load_attempted = False

    def _ensure_model(self) -> None:
        """Attempt to load the OpenAI Whisper model if available."""
        if self.simulation_mode:
            logger.info("Simulation mode active: Whisper model loading skipped.")
            return
        if self._model_load_attempted:
            return

        self._model_load_attempted = True
        self.last_status = "loading_model"

        try:
            import whisper  # type: ignore

            logger.info(
                "Loading Whisper model '%s' on %s...", self.model_name, self.device
            )
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Whisper model '%s' successfully loaded.", self.model_name)
        except ImportError:
            logger.info(
                "openai-whisper not installed; using SpeechRecognition (Google Web Speech API) for STT."
            )
            self.model = None
        except Exception as exc:
            logger.error(
                "Failed to load Whisper model '%s': %s. Real transcription unavailable.",
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

    def get_language(self) -> str:
        """Return currently configured STT language code."""
        return self.language

    def set_language(self, lang_code: str) -> bool:
        """Configure STT language code (e.g. en-US, hi-IN, ne-NP)."""
        clean = lang_code.strip()
        if clean in self.supported_languages:
            self.language = clean
            logger.info("STT language configured to %s", self.language)
            return True
        logger.warning("Language %s not in supported list %s; defaulting to en-US", clean, self.supported_languages)
        self.language = "en-US"
        return False

    def transcribe(self, audio_file_path: str, fallback_to_whisper: bool = True) -> str:
        """Transcribe an audio file into text.

        Uses speech_recognition (Google Web Speech API) as primary fast engine,
        Whisper model as secondary, and simulated fallback in simulation mode.

        Args:
            audio_file_path: Absolute or relative path to the audio file.
            fallback_to_whisper: Whether to fall back to local Whisper model when
                cloud STT reports unintelligible speech or silence.

        Returns:
            str: Transcribed text or simulated transcription.
        """
        if self.simulation_mode:
            self.last_status = "simulated"
            return self.transcribe_simulated()

        self.last_status = "no_audio"
        if not os.path.exists(audio_file_path):
            logger.warning(
                "Audio file '%s' not found for transcription.",
                audio_file_path,
            )
            return ""

        # Check for empty file
        if os.path.getsize(audio_file_path) < 100:
            logger.debug("Audio file is empty (<100 bytes).")
            return ""

        # Check audio energy before attempting cloud/local STT to avoid unnecessary queries on silence
        try:
            with wave.open(audio_file_path, "rb") as wf:
                n_frames = wf.getnframes()
                if n_frames > 0:
                    raw_bytes = wf.readframes(n_frames)
                    import struct, math
                    samples = struct.unpack(f"{n_frames * wf.getnchannels()}h", raw_bytes)
                    rms = math.sqrt(sum(s * s for s in samples) / max(1, len(samples)))
                    if rms < 25.0:
                        self.last_status = "silence"
                        logger.debug("Audio file is near-silent (RMS: %.2f), skipping STT", rms)
                        return ""
        except Exception:
            pass

        # 1. Primary fast speech recognition via SpeechRecognition (Google Web Speech API)
        # Import it independently so an optional dependency absence cannot
        # cause an UnboundLocalError in an exception clause.
        try:
            import speech_recognition as sr
        except ImportError:
            sr = None
            logger.debug("SpeechRecognition is not installed; trying local Whisper fallback.")

        if sr is not None:
            try:
                self.last_status = "recognizing"
                recognizer = sr.Recognizer()
                # Cloud recognition must not leave the sole capture owner stuck
                # indefinitely with a misleading standby heartbeat.
                recognizer.operation_timeout = 8.0
                recognizer.energy_threshold = 60
                recognizer.dynamic_energy_threshold = True
                with sr.AudioFile(audio_file_path) as source:
                    audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data, language=self.language)
                except Exception:
                    if self.language != "en-US":
                        # Fallback to English if regional recognition fails
                        text = recognizer.recognize_google(audio_data, language="en-US")
                    else:
                        raise
                if text and text.strip():
                    self.last_status = "recognized"
                    logger.debug("SpeechRecognition produced a transcript")
                    return text.strip()
            except sr.UnknownValueError:
                self.last_status = "unintelligible"
                if not fallback_to_whisper:
                    logger.debug("Google Speech Recognition returned unintelligible; fast mode skipping Whisper.")
                    return ""
                logger.debug("Google Speech Recognition could not understand audio (unintelligible or silence); attempting local Whisper fallback.")
            except sr.RequestError as req_err:
                logger.warning("Google Speech Recognition service request failed: %s", req_err)
            except Exception as exc:
                logger.debug("SpeechRecognition recognize_google: %s", exc)

        # 2. Local Whisper fallback. It is initialized only when it is needed,
        # not while FastAPI is importing the voice routes.
        if not fallback_to_whisper and sr is not None:
            return ""

        self._ensure_model()
        if self.model is not None:
            try:
                self.last_status = "recognizing"
                logger.info("Transcribing audio file with Whisper: %s", audio_file_path)
                whisper_lang = (self.language or "en-US").split("-")[0].lower()
                result = self.model.transcribe(
                    audio_file_path,
                    fp16=False,
                    language=whisper_lang,
                    temperature=0.0,
                    condition_on_previous_text=False,
                    no_speech_threshold=0.6,
                    logprob_threshold=-1.0,
                )
                transcription = str(result.get("text", "")).strip()
                if transcription:
                    self.last_status = "recognized"
                    logger.debug("Whisper produced a transcript: %s", transcription)
                    return transcription
                self.last_status = "unintelligible"
            except Exception as exc:
                self.last_status = "failed"
                logger.error("Whisper transcription failed: %s", exc)
        else:
            self.last_status = "unavailable"

        return ""

    def record_audio(
        self,
        duration_secs: int = 4,
        output_path: Optional[str] = None,
        device: Optional[str] = None,
    ) -> bool:
        """Record audio to output_path using PipeWire pw-record or ALSA arecord.

        Args:
            duration_secs: Recording duration in seconds.
            output_path: Target path for the recorded WAV file.
            device: Optional ALSA device identifier (e.g. 'plughw:2,0').

        Returns:
            bool: True if recording succeeded or was simulated, False on error.
        """
        # Handle swapped or defaulted arguments safely
        if isinstance(duration_secs, str) and (output_path is None or isinstance(output_path, int)):
            output_path, duration_secs = duration_secs, output_path or 4
        if output_path is None:
            output_path = "/tmp/jarvis_recorded.wav"

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

        # 1. Primary: PipeWire native recorder (ideal for Debian 13 / Pi 5, avoids device lock conflicts)
        if shutil.which("pw-record"):
            try:
                pw_cmd = ["pw-record", "--rate=16000", "--channels=1", "--format=s16", output_path]
                logger.info("Recording %ds via pw-record to %s", duration_secs, output_path)
                import time
                pw_proc = subprocess.Popen(pw_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                time.sleep(duration_secs)
                pw_proc.terminate()
                try:
                    _, err = pw_proc.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    pw_proc.kill()
                    _, err = pw_proc.communicate(timeout=1)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                    logger.info("Successfully recorded %d seconds via pw-record (%d bytes)", duration_secs, os.path.getsize(output_path))
                    return True
                else:
                    logger.warning("pw-record finished without expected audio file: err=%s", err.decode() if err else "")
            except Exception as e:
                logger.warning("pw-record failed: %s; trying arecord.", e)

        # 2. Secondary: ALSA arecord with plughw format conversion
        if shutil.which("arecord"):
            rec_dev = device
            if not rec_dev or rec_dev == "default":
                try:
                    from apps.voice.audio_manager import AudioManager
                    mgr = AudioManager()
                    best = mgr.select_best_device()
                    rec_dev = mgr.get_device_alsa_identifier(best, plug=True)
                except Exception:
                    rec_dev = "plughw:2,0"

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
                if proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                    logger.info("Recorded %d seconds of audio to %s", duration_secs, output_path)
                    return True
                logger.warning("arecord failed with code %d: %s", proc.returncode, proc.stderr.strip())
            except Exception as exc:
                logger.error("Error during arecord execution: %s", exc)

        logger.error("All physical audio recording backends failed for %s", output_path)
        return False

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
