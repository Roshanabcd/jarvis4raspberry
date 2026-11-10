"""Wake Word Detector for JARVIS OS.

Provides wake word detection on transcribed text or streaming audio frames.
Currently uses keyword matching on transcribed text with future integration
hooks for Picovoice Porcupine and openWakeWord.
"""

import logging
import re
from typing import Optional

from config.config_manager import config

logger = logging.getLogger("JARVIS-WAKEWORD")


class WakeWordDetector:
    """Detects configured wake words to activate JARVIS OS."""

    def __init__(
        self,
        wake_word: Optional[str] = None,
        simulation_mode: Optional[bool] = None,
    ):
        """Initialize wake word detector.

        Args:
            wake_word: Optional explicit wake word. If None, reads 'wake_word'
                from config.yaml (defaults to 'jarvis').
            simulation_mode: Explicit flag for simulation mode.
        """
        if wake_word is not None:
            self.wake_word = wake_word.strip().lower()
        else:
            configured = config.get("wake_word", "jarvis")
            self.wake_word = str(configured).strip().lower()

        if simulation_mode is not None:
            self.simulation_mode = simulation_mode
        else:
            voice_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
            if "simulation_mode" in voice_cfg:
                self.simulation_mode = bool(voice_cfg["simulation_mode"])
            else:
                self.simulation_mode = bool(config.get("simulation_mode", False))

        # TODO: Picovoice Porcupine integration hook
        # import pvporcupine
        # access_key = config.get("porcupine_access_key")
        # if access_key and not self.simulation_mode:
        #     self._porcupine = pvporcupine.create(
        #         access_key=access_key,
        #         keywords=[self.wake_word]
        #     )

        # TODO: openWakeWord integration hook
        # from openwakeword.model import Model
        # if not self.simulation_mode:
        #     self._oww_model = Model(wakeword_models=[f"{self.wake_word}.onnx"])

        logger.info(
            "WakeWordDetector initialized (wake_word='%s', simulation_mode=%s)",
            self.wake_word,
            self.simulation_mode,
        )

    def detect(self, audio_text: str) -> bool:
        """Check if the wake word appears in the transcribed audio text.

        Performs a case-insensitive check and handles punctuation/boundaries.

        Args:
            audio_text: The transcribed text to inspect.

        Returns:
            bool: True if the wake word is detected, False otherwise.
        """
        if not audio_text or not isinstance(audio_text, str):
            return False

        normalized_text = audio_text.strip().lower()

        # Word boundary or containment check
        pattern = r"\b" + re.escape(self.wake_word) + r"\b"
        if re.search(pattern, normalized_text):
            logger.info("Wake word '%s' detected in text: '%s'", self.wake_word, audio_text)
            return True

        # Acoustic/STT phonetic variations if wake word is jarvis
        if self.wake_word == "jarvis":
            variations = [r"\bjarvis\b", r"\bjarves\b", r"\bjavis\b", r"\bjar\s*vis\b", r"\bhey\s+jarvis\b"]
            for var in variations:
                if re.search(var, normalized_text):
                    logger.info("Wake word variation matched in text: '%s'", audio_text)
                    return True

        # Fallback substring check in case punctuation or spelling attaches to it
        if self.wake_word in normalized_text:
            logger.info(
                "Wake word '%s' detected as substring in: '%s'",
                self.wake_word,
                audio_text,
            )
            return True

        return False

    def detect_stream(self, audio_frame: bytes) -> bool:
        """Hook for real-time audio buffer stream processing.

        Args:
            audio_frame: Raw PCM audio bytes.

        Returns:
            bool: True if wake word detected in stream.
        """
        # TODO: Real-time stream detection using Porcupine or openWakeWord:
        # if hasattr(self, '_porcupine') and self._porcupine:
        #     pcm = struct.unpack_from("h" * self._porcupine.frame_length, audio_frame)
        #     result = self._porcupine.process(pcm)
        #     return result >= 0
        # elif hasattr(self, '_oww_model') and self._oww_model:
        #     prediction = self._oww_model.predict(audio_frame)
        #     return prediction.get(self.wake_word, 0.0) > 0.5

        logger.debug("Streaming wake word detection hook called (stub)")
        return False
