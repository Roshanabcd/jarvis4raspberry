"""Text-to-Speech (TTS) Module for JARVIS OS.

Supports speech synthesis via pyttsx3, subprocess espeak/espeak-ng, and
graceful simulation mode fallback.
"""

import asyncio
import logging
import shutil
import subprocess
from typing import Any, Dict, Optional

from config.config_manager import config

logger = logging.getLogger("JARVIS-TTS")


class TextToSpeech:
    """Handles text-to-speech synthesis with multiple backend options."""

    def __init__(
        self,
        engine_type: Optional[str] = None,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        language: Optional[str] = None,
        simulation_mode: Optional[bool] = None,
    ):
        """Initialize TTS engine.

        Args:
            engine_type: Desired engine ('pyttsx3', 'espeak', etc.). Defaults to config.
            rate: Speech speed rate (words per minute). Defaults to config.
            volume: Speech volume (0.0 to 1.0). Defaults to config.
            language: Speech language code (e.g. 'en'). Defaults to config.
            simulation_mode: Explicit flag for simulation mode. Defaults to config.
        """
        voice_cfg: Dict[str, Any] = config.get("voice", {})

        self.rate = rate if rate is not None else int(voice_cfg.get("rate", 150))
        self.volume = volume if volume is not None else float(voice_cfg.get("volume", 0.9))
        self.language = language or str(voice_cfg.get("language", "en"))
        self.configured_engine = engine_type or str(voice_cfg.get("engine", "espeak"))

        if simulation_mode is not None:
            self.simulation_mode = simulation_mode
        else:
            self.simulation_mode = bool(config.get("simulation_mode", True))

        self.backend: str = "simulated"
        self._pyttsx3_engine = None
        self._espeak_cmd: Optional[str] = None

        self._init_backend()

    def _init_backend(self) -> None:
        """Probe and initialize available TTS backends."""
        if self.simulation_mode:
            logger.info("Simulation mode active: TTS using simulated audio output.")
            self.backend = "simulated"
            return

        # 1. Try pyttsx3 first
        try:
            import pyttsx3  # type: ignore

            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            self._pyttsx3_engine = engine
            self.backend = "pyttsx3"
            logger.info("Initialized pyttsx3 TTS backend successfully.")
            return
        except ImportError:
            logger.debug("pyttsx3 library not installed.")
        except Exception as exc:
            logger.warning("Failed to initialize pyttsx3: %s", exc)

        # 2. Try espeak / espeak-ng subprocess
        espeak_bin = shutil.which("espeak") or shutil.which("espeak-ng")
        if espeak_bin:
            self._espeak_cmd = espeak_bin
            self.backend = "espeak"
            logger.info("Initialized espeak TTS backend using binary: %s", espeak_bin)
            return

        # 3. Both unavailable -> log warning and simulate
        logger.warning(
            "Neither pyttsx3 nor espeak is available on this system. Falling back to simulation mode."
        )
        self.backend = "simulated"

    async def speak(self, text: str) -> None:
        """Synthesize and speak the given text asynchronously.

        Args:
            text: The text to be spoken.
        """
        if not text or not text.strip():
            return

        clean_text = text.strip()

        if self.simulation_mode or self.backend == "simulated":
            logger.info("[TTS Simulated Voice Output]: %s", clean_text)
            return

        if self.backend == "pyttsx3":
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._speak_pyttsx3_blocking, clean_text)
            except Exception as exc:
                logger.error("pyttsx3 synthesis failed: %s; falling back to simulated", exc)
                logger.info("[TTS Simulated Voice Output]: %s", clean_text)
            return

        if self.backend == "espeak":
            try:
                await self._speak_espeak(clean_text)
            except Exception as exc:
                logger.error("espeak synthesis failed: %s; falling back to simulated", exc)
                logger.info("[TTS Simulated Voice Output]: %s", clean_text)
            return

    def _speak_pyttsx3_blocking(self, text: str) -> None:
        """Run pyttsx3 speak synchronously in a separate thread.

        Args:
            text: Text to speak.
        """
        if self._pyttsx3_engine is None:
            return
        self._pyttsx3_engine.say(text)
        self._pyttsx3_engine.runAndWait()

    async def _speak_espeak(self, text: str) -> None:
        """Run espeak subprocess asynchronously.

        Args:
            text: Text to speak.
        """
        bin_path = self._espeak_cmd or "espeak"
        # Amplitude/volume in espeak is roughly 0-200, default is 100
        amplitude = max(0, min(200, int(self.volume * 100)))

        cmd = [
            bin_path,
            "-s",
            str(self.rate),
            "-a",
            str(amplitude),
            "-v",
            self.language,
            text,
        ]

        logger.debug("Executing espeak: %s", " ".join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            logger.warning(
                "espeak returned non-zero code %d: %s",
                process.returncode,
                stderr.decode().strip(),
            )

    def speak_sync(self, text: str) -> None:
        """Synchronous helper for speak() when called from non-async contexts.

        Args:
            text: The text to be spoken.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Scheduled in running loop
                asyncio.run_coroutine_threadsafe(self.speak(text), loop)
            else:
                loop.run_until_complete(self.speak(text))
        except RuntimeError:
            asyncio.run(self.speak(text))
