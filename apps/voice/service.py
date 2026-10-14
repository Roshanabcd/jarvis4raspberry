"""Voice Service for JARVIS OS.

Orchestrates the entire voice interaction pipeline:
AudioManager -> WakeWordDetector -> SpeechToText -> MainAgent -> TextToSpeech
with stateful dialogue tracking via ConversationManager.
"""

import logging
import os
import tempfile
import threading
from typing import Any, Dict, Optional

from apps.voice.audio_manager import AudioManager
from apps.voice.conversation import ConversationManager
from apps.voice.stt import SpeechToText
from apps.voice.tts import TextToSpeech
from apps.voice.wake_word import WakeWordDetector
from config.config_manager import config

logger = logging.getLogger("JARVIS-VOICE")


class VoiceService:
    """End-to-end voice service managing background listening and command processing."""

    def __init__(
        self,
        wake_word: Optional[str] = None,
        simulation_mode: Optional[bool] = None,
    ):
        """Initialize the VoiceService and underlying voice sub-components.

        Args:
            wake_word: Optional wake word string override.
            simulation_mode: Optional simulation mode override.
        """
        if simulation_mode is not None:
            self.simulation_mode = simulation_mode
        else:
            self.simulation_mode = bool(config.get("simulation_mode", True))

        self.audio_manager = AudioManager(simulation_mode=self.simulation_mode)
        self.wake_detector = WakeWordDetector(
            wake_word=wake_word,
            simulation_mode=self.simulation_mode,
        )
        self.stt = SpeechToText(simulation_mode=self.simulation_mode)
        self.tts = TextToSpeech(simulation_mode=self.simulation_mode)
        self.conversation = ConversationManager()

        self.listening: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._selected_device: Optional[Dict[str, Any]] = None
        self._main_agent = None

        # Temporary audio directory for chunk processing
        self._temp_dir = os.path.join(tempfile.gettempdir(), "jarvis_voice")
        os.makedirs(self._temp_dir, exist_ok=True)

        logger.info(
            "VoiceService initialized (wake_word='%s', simulation_mode=%s)",
            self.wake_detector.wake_word,
            self.simulation_mode,
        )

    def start(self) -> None:
        """Start the background audio listening loop in a dedicated daemon thread."""
        if self.listening:
            logger.warning("VoiceService is already running.")
            return

        self.listening = True
        self._stop_event.clear()
        self._selected_device = self.audio_manager.select_best_device()

        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="JARVIS-VoiceListener",
        )
        self._thread.start()
        logger.info(
            "VoiceService started. Waiting for wake word '%s'...",
            self.wake_detector.wake_word,
        )

    def _listen_loop(self) -> None:
        """Background listening thread.

        Pipeline per iteration:
        1. Record 2s audio chunk
        2. Transcribe chunk
        3. Check wake word
        4. If detected:
           a. Speak 'Yes?'
           b. Record 5s command
           c. Transcribe command
           d. Process command
        """
        device_id = self.audio_manager.get_device_alsa_identifier(self._selected_device)
        chunk_file = os.path.join(self._temp_dir, "wake_chunk.wav")
        cmd_file = os.path.join(self._temp_dir, "command.wav")

        while self.listening and not self._stop_event.is_set():
            try:
                # 1. Record 2s audio chunk
                recorded = self.stt.record_audio(
                    duration_secs=2,
                    output_path=chunk_file,
                    device=device_id,
                )

                if not recorded or self._stop_event.is_set():
                    if self.simulation_mode:
                        self._stop_event.wait(1.0)
                    continue

                # 2. Transcribe chunk
                text = self.stt.transcribe(chunk_file)

                # 3. Check wake word
                if text and self.wake_detector.detect(text):
                    logger.info("Wake word '%s' detected!", self.wake_detector.wake_word)

                    # 4a. Acknowledge wake word
                    self.tts.speak_sync("Yes?")

                    # 4b. Record 5s command
                    cmd_recorded = self.stt.record_audio(
                        duration_secs=5,
                        output_path=cmd_file,
                        device=device_id,
                    )

                    if cmd_recorded and not self._stop_event.is_set():
                        # 4c. Transcribe command
                        cmd_text = self.stt.transcribe(cmd_file)
                        if cmd_text and cmd_text.strip():
                            # 4d. Process command
                            self.process_command(cmd_text)

                # Throttle loop iterations in simulation mode to avoid burning CPU
                if self.simulation_mode:
                    self._stop_event.wait(1.0)
                else:
                    self._stop_event.wait(0.1)

            except Exception as exc:
                logger.error("Error in voice listen loop: %s", exc)
                self._stop_event.wait(1.0)

    def process_command(self, text: str) -> str:
        """Process a spoken or text command through the JARVIS Brain and speak the reply."""
        logger.info("Processing voice command: '%s'", text)
        self.conversation.add_turn(role="user", text=text)

        response: str = ""
        try:
            from ai.brain import get_brain
            brain = get_brain()
            result = brain.chat(user_message=text, use_tools=True)
            response = result.get("response", "")
            tools_used = result.get("tools_used", [])
            if tools_used:
                logger.info("Tools used: %s", [t["tool"] for t in tools_used])
        except Exception as exc:
            logger.warning("Brain error: %s", exc)
            response = f"I received your command: {text}"

        if not response:
            response = f"Understood: {text}"

        self.conversation.add_turn(role="assistant", text=response)
        try:
            self.tts.speak_sync(response)
        except Exception as exc:
            logger.error("TTS error: %s", exc)
        return response


    def stop(self) -> None:
        """Stop background listening loop and cleanly terminate thread."""
        self.listening = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info("VoiceService stopped.")


# Module-level singleton instance for API routes and imports
voice_service = VoiceService()
