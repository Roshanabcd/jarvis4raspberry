"""Voice Service for JARVIS OS.

Orchestrates the entire voice interaction pipeline:
AudioManager -> WakeWordDetector -> SpeechToText -> MainAgent -> TextToSpeech
with stateful dialogue tracking via ConversationManager.
"""

import logging
import os
import queue
import tempfile
import threading
from typing import Any, Dict, Optional

from apps.voice.audio_manager import AudioManager
from apps.voice.conversation import ConversationManager
from apps.voice.stt import SpeechToText
from apps.voice.tts import TextToSpeech
from apps.voice.wake_word import WakeWordDetector
from apps.voice.voice_jobs import VoiceJob, VoiceJobManager, voice_job_mgr
from config.config_manager import config

logger = logging.getLogger("JARVIS-VOICE")


class VoiceService:
    """End-to-end voice service managing background listening and command processing."""

    def __init__(
        self,
        wake_word: Optional[str] = None,
        simulation_mode: Optional[bool] = None,
        reply_queue_capacity: int = 32,
        job_manager: Optional[VoiceJobManager] = None,
    ):
        """Initialize the VoiceService and underlying voice sub-components.

        Args:
            wake_word: Optional wake word string override.
            simulation_mode: Optional simulation mode override.
        """
        if simulation_mode is not None:
            self.simulation_mode = simulation_mode
        else:
            voice_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
            if "simulation_mode" in voice_cfg:
                self.simulation_mode = bool(voice_cfg["simulation_mode"])
            else:
                self.simulation_mode = False

        self.audio_manager = AudioManager(simulation_mode=self.simulation_mode)
        self.wake_detector = WakeWordDetector(
            wake_word=wake_word,
            simulation_mode=self.simulation_mode,
        )
        self.stt = SpeechToText(simulation_mode=self.simulation_mode)
        self.tts = TextToSpeech(simulation_mode=self.simulation_mode)
        self.conversation = ConversationManager()

        self.listening: bool = False
        self.state: str = "STANDBY"
        self._muted: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._selected_device: Optional[Dict[str, Any]] = None
        self._main_agent = None
        if reply_queue_capacity < 1:
            raise ValueError("reply_queue_capacity must be at least 1")
        self._reply_queue: "queue.Queue[VoiceJob]" = queue.Queue(maxsize=reply_queue_capacity)
        self._reply_enqueue_lock = threading.Lock()
        self._job_manager = job_manager or voice_job_mgr
        self._delivery_stop = threading.Event()
        self._delivery_worker: Optional[threading.Thread] = None
        self._last_staged: Dict[str, Any] = {}
        self._speech_generation: int = 0

        # Temporary audio directory for chunk processing
        self._temp_dir = os.path.join(tempfile.gettempdir(), "jarvis_voice")
        os.makedirs(self._temp_dir, exist_ok=True)

        logger.info(
            "VoiceService initialized (wake_word='%s', simulation_mode=%s)",
            self.wake_detector.wake_word,
            self.simulation_mode,
        )

    def enqueue_response(
        self,
        response: str,
        *,
        broadcast: bool = False,
        preempt: bool = False,
        turn_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> VoiceJob:
        """Queue one tracked reply, refusing capacity rather than evicting live work unless preempt is True."""
        if not isinstance(response, str) or not response.strip():
            raise ValueError("response must be a non-empty string")
        with self._reply_enqueue_lock:
            if preempt:
                self.stop_playback()
            self._ensure_delivery_worker()
            if self._reply_queue.full():
                raise RuntimeError("Voice reply queue is full")
            current_gen = getattr(self, "_speech_generation", 0)
            job = self._job_manager.create_job(
                response,
                preserve_active=True,
                generation=current_gen,
                turn_id=turn_id,
                message_id=message_id,
            )
            self._reply_queue.put_nowait(job)
        if broadcast:
            try:
                from apps.api.websocket_api import broadcast_chat_message
                broadcast_chat_message(
                    role="assistant",
                    text=response,
                    message_id=message_id or turn_id or job.job_id,
                    turn_id=turn_id or job.job_id,
                    playback_target="system",
                )
            except Exception as exc:
                logger.debug("Failed to broadcast queued assistant reply: %s", exc)
        return job

    def _ensure_delivery_worker(self) -> None:
        """Start delivery lazily, without opening a capture or playback device."""
        if self._delivery_worker and self._delivery_worker.is_alive():
            if self._delivery_stop.is_set():
                raise RuntimeError("Voice reply delivery is stopping")
            return
        self._delivery_stop.clear()
        self._delivery_worker = threading.Thread(
            target=self._delivery_loop, name="voice-reply-delivery", daemon=True,
        )
        self._delivery_worker.start()

    def cancel_response(self, job_id: str) -> Optional[VoiceJob]:
        """Cancel a reply atomically; stop playback only after recording cancellation."""
        cancelled, was_active = self._job_manager.cancel_job(job_id)
        if was_active and cancelled and cancelled.status == "cancelled":
            try:
                from apps.voice.speech_manager import speech_manager
                speech_manager.stop(expected_owner=job_id)
            except Exception:
                logger.exception("Failed to stop playback after cancelling voice job %s", job_id)
        return cancelled

    def _delivery_loop(self) -> None:
        while not self._delivery_stop.is_set():
            try:
                job = self._reply_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                self.process_one_job(job)
            finally:
                self._reply_queue.task_done()

    def process_one_job(self, job: VoiceJob) -> VoiceJob:
        """Run synthesis, staging, and blocking playback for one queued reply."""
        current = self._job_manager.get_job(job.job_id)
        if not current or current.status != "queued":
            return current or job
        current_gen = getattr(self, "_speech_generation", 0)
        job_gen = getattr(job, "generation", 0)
        if job_gen != current_gen:
            logger.info("Dropping preempted voice job %s (generation %d != %d)", job.job_id, job_gen, current_gen)
            cancelled = self._job_manager.update_job(job.job_id, status="cancelled", error="Preempted by newer speech")
            return cancelled or job
        try:
            current = self._job_manager.update_job(job.job_id, status="synthesizing")
            if not current or current.status != "synthesizing":
                return job
            from apps.voice.speech_manager import speech_manager
            staged = speech_manager.synthesize_and_stage(job.text, play_system=False)
            if (
                not isinstance(staged, dict)
                or staged.get("status") != "ok"
                or staged.get("success") is not True
                or not staged.get("audio_id")
            ):
                error = staged.get("error") if isinstance(staged, dict) else None
                raise RuntimeError(error or "Speech synthesis failed")

            if getattr(job, "generation", 0) != getattr(self, "_speech_generation", 0):
                logger.info("Dropping preempted synthesized audio for job %s", job.job_id)
                cancelled = self._job_manager.update_job(job.job_id, status="cancelled", error="Preempted by newer speech")
                return cancelled or job

            current = self._job_manager.update_job(
                job.job_id,
                audio_id=staged.get("audio_id"),
                audio_url=staged.get("audio_url"),
                provider=staged.get("provider"),
                is_cloned=bool(staged.get("is_cloned", False)),
                latency_ms=staged.get("latency_ms"),
            )
            if not current or current.status != "synthesizing":
                return current or job
            audio = speech_manager.get_staged_audio(staged["audio_id"])
            if not audio:
                raise RuntimeError("Speech synthesis did not produce staged audio")
            current = self._job_manager.update_job(job.job_id, status="playing")
            if not current or current.status != "playing":
                return current or job

            if staged.get("audio_url"):
                try:
                    from apps.api.websocket_api import broadcast_chat_message
                    broadcast_chat_message(
                        role="assistant",
                        text=job.text,
                        audio_url=staged.get("audio_url"),
                        message_id=getattr(job, "message_id", None) or getattr(job, "turn_id", None) or job.job_id,
                        turn_id=getattr(job, "turn_id", None) or job.job_id,
                        playback_target="system",
                        provider_label=staged.get("provider_label"),
                        is_cloned=bool(staged.get("is_cloned", False)),
                    )
                except Exception as b_err:
                    logger.debug("Failed to broadcast staged audio URL: %s", b_err)

            played = speech_manager.play_system_audio(
                audio[0],
                wait=True,
                playback_owner=job.job_id,
                should_play=lambda: (
                    getattr(job, "generation", 0) == getattr(self, "_speech_generation", 0)
                    and (latest := self._job_manager.get_job(job.job_id)) is not None
                    and latest.status == "playing"
                ),
            )
            if not played:
                raise RuntimeError("System audio playback failed")
            return self._job_manager.update_job(job.job_id, status="completed") or job
        except Exception as exc:
            logger.error("Voice reply delivery failed for %s: %s", job.job_id, exc)
            failed = self._job_manager.update_job(job.job_id, status="failed", error=str(exc))
            return failed or job

    def mute(self) -> None:
        """Mute voice input processing."""
        self._muted = True
        self.state = "MUTED"
        try:
            from apps.voice.wake_word_engine import wake_word_engine
            wake_word_engine.mute()
        except Exception:
            pass
        logger.info("VoiceService muted.")

    def unmute(self) -> None:
        """Unmute voice input processing."""
        self._muted = False
        self.state = "LISTENING" if self.listening else "STANDBY"
        try:
            from apps.voice.wake_word_engine import wake_word_engine
            wake_word_engine.unmute()
        except Exception:
            pass
        logger.info("VoiceService unmuted.")

    def stop_playback(self) -> None:
        """Interrupt any ongoing audio synthesis playback immediately (barge-in)."""
        try:
            self._speech_generation = getattr(self, "_speech_generation", 0) + 1
            with self._reply_enqueue_lock:
                while not self._reply_queue.empty():
                    try:
                        old_job = self._reply_queue.get_nowait()
                        self._job_manager.cancel_job(old_job.job_id)
                        self._reply_queue.task_done()
                    except queue.Empty:
                        break
            self._job_manager.cancel_active_jobs()
            from apps.voice.speech_manager import speech_manager
            speech_manager.stop()
        except Exception as e:
            logger.debug("stop_playback error: %s", e)

    def is_muted(self) -> bool:
        """Return mute state."""
        return self._muted

    def get_state(self) -> Dict[str, Any]:
        """Return the current active voice service status dictionary."""
        try:
            from apps.voice.wake_word_engine import wake_word_engine
            ww_status = wake_word_engine.get_status()
            active = bool(self.listening and wake_word_engine._is_running)
            if self.simulation_mode:
                curr_state = "MUTED" if self._muted else ("LISTENING" if self.listening else "STANDBY")
            elif wake_word_engine._is_running:
                curr_state = ww_status.get("state", "STANDBY")
            else:
                curr_state = "MUTED" if self._muted else ("LISTENING" if active else "STANDBY")
        except Exception:
            active = self.listening
            curr_state = "MUTED" if self._muted else ("LISTENING" if active else "STANDBY")
            ww_status = {}

        return {
            "state": curr_state,
            "listening": active,
            "muted": self._muted or (curr_state == "MUTED"),
            "device": self._selected_device or self.audio_manager.select_best_device(),
            "wake_word": self.wake_detector.wake_word,
            "microphone_available": self.audio_manager.is_microphone_available(),
            "wake_engine": ww_status,
        }

    def start(self) -> None:
        """Start the background audio listening loop in a dedicated daemon thread."""
        if self.listening:
            logger.warning("VoiceService is already running.")
            return

        self.listening = True
        self.state = "MUTED" if self._muted else "LISTENING"
        self._selected_device = self.audio_manager.select_best_device()

        try:
            from apps.voice.wake_word_engine import wake_word_engine
            wake_word_engine.start()
            self._thread = wake_word_engine._thread
            logger.info("VoiceService started via WakeWordEngine (12-state silence machine).")
        except Exception as exc:
            self.listening = False
            self.state = "ERROR"
            logger.error("Failed to start WakeWordEngine: %s", exc)

    def listen_once(self, duration_secs: int = 4) -> Dict[str, Any]:
        """One-shot push-to-talk voice capture, transcription, and command execution."""
        import time
        if self._muted:
            return {"status": "error", "message": "Microphone is muted"}

        from apps.voice.wake_word_engine import is_voice_service_daemon_running
        daemon_active = False
        try:
            daemon_active = is_voice_service_daemon_running()
        except Exception:
            daemon_active = False

        if daemon_active:
            return {
                "status": "error",
                "message": "The dedicated voice daemon owns the microphone; no second capture started.",
            }

        was_running = False
        try:
            from apps.voice.wake_word_engine import wake_word_engine
            was_running = wake_word_engine._is_running
            if was_running:
                wake_word_engine.mute()
        except Exception:
            pass

        prev_state = self.state
        self.state = "LISTENING"
        cmd_file = os.path.join(self._temp_dir, f"cmd_once_{int(time.time())}.wav")
        dev = self._selected_device or self.audio_manager.select_best_device()
        device_id = self.audio_manager.get_device_alsa_identifier(dev, plug=True)

        try:
            recorded = self.stt.record_audio(duration_secs=duration_secs, output_path=cmd_file, device=device_id)
            if not recorded:
                self.state = prev_state
                return {"status": "error", "message": "Failed to capture audio from microphone"}

            self.state = "PROCESSING"
            text = self.stt.transcribe(cmd_file)
            if not text or not text.strip():
                self.state = prev_state
                return {"status": "empty", "transcribed": "", "message": "No audible speech recognized"}

            response = self.process_command(text)
            self.state = prev_state
            staged = getattr(self, "_last_staged", {}) or {}
            return {
                "status": "ok",
                "transcribed": text,
                "response": response,
                "job_id": staged.get("job_id"),
                "job_status": staged.get("status"),
                "audio_error": staged.get("error"),
                "audio_id": staged.get("audio_id"),
                "audio_url": staged.get("audio_url"),
                "provider": staged.get("provider"),
                "provider_label": staged.get("provider_label"),
            }
        except Exception as e:
            self.state = prev_state
            logger.error("Error in listen_once: %s", e)
            return {"status": "error", "message": str(e)}
        finally:
            if was_running:
                try:
                    from apps.voice.wake_word_engine import wake_word_engine
                    wake_word_engine.unmute()
                except Exception:
                    pass

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
        device_id = self.audio_manager.get_device_alsa_identifier(self._selected_device, plug=True)
        chunk_file = os.path.join(self._temp_dir, "wake_chunk.wav")
        cmd_file = os.path.join(self._temp_dir, "command.wav")

        while self.listening and not self._stop_event.is_set():
            if self._muted:
                self._stop_event.wait(0.5)
                continue
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
                    # Barge-in: interrupt any currently playing audio immediately
                    self.stop_playback()

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

    def process_command(
        self,
        text: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        role: Optional[str] = None,
        speak: bool = True,
    ) -> str:
        """Process a spoken or text command through the JARVIS Brain and speak the reply."""
        self.stop_playback()
        logger.info("Processing voice command: '%s'", text)
        self.conversation.add_turn(role="user", text=text)
        try:
            from apps.api.websocket_api import broadcast_chat_message
            broadcast_chat_message(role="user", text=text)
        except Exception as e:
            logger.debug("Failed to broadcast user chat message: %s", e)

        # The identity used for authorization is always resolved locally.  Do
        # not trust optional identity arguments supplied by a caller: a voice
        # client must not be able to claim an ADMIN role in its JSON payload.
        try:
            from apps.voice.session_manager import voice_session_mgr
            sess = voice_session_mgr.get_active_session()
            user_id = sess.user_id
            session_id = sess.session_id
            role = sess.authorization_role()
        except Exception:
            user_id = "guest"
            session_id = "voice-session"
            role = "GUEST"

        response: str = ""
        try:
            from ai.brain import get_brain
            brain = get_brain()
            result = brain.chat(user_message=text, session_id=session_id, user_id=user_id, role=role, use_tools=True)
            response = result.get("response", "")
            tools_used = result.get("tools_used", [])
            if tools_used:
                logger.info("Tools used: %s", [t["tool"] for t in tools_used])
        except Exception as exc:
            logger.warning("Brain error: %s", exc)
            response = "I could not complete that request because the AI service failed. Check the provider status before retrying."

        if not response:
            response = "The AI service returned no answer. Completion could not be verified."

        turn_id = f"vcmd_{uuid.uuid4().hex[:10]}"
        self.conversation.add_turn(role="assistant", text=response)
        spoken_text = (result.get("spoken_summary") or response) if isinstance(result, dict) else response
        if speak:
            self.speak_response(spoken_text, turn_id=turn_id)
        else:
            try:
                from apps.api.websocket_api import broadcast_chat_message
                broadcast_chat_message(
                    role="assistant",
                    text=response,
                    message_id=turn_id,
                    turn_id=turn_id,
                    playback_target="system",
                )
            except Exception:
                logger.debug("Could not broadcast voice reply")
        return response

    def speak_response(self, response: str, *, broadcast: bool = True, turn_id: Optional[str] = None) -> Dict[str, Any]:
        """Synthesize and stage a reply for browser and system delivery."""
        self._last_staged = {}
        try:
            from apps.voice.speech_manager import speech_manager
            staged = speech_manager.synthesize_and_stage(response)
            self._last_staged = staged or {}
            tid = turn_id or f"vcmd_{uuid.uuid4().hex[:10]}"
            if broadcast:
                try:
                    from apps.api.websocket_api import broadcast_chat_message
                    broadcast_chat_message(
                        role="assistant",
                        text=response,
                        audio_url=staged.get("audio_url") if isinstance(staged, dict) else None,
                        message_id=tid,
                        turn_id=tid,
                        playback_target="system",
                        provider_label=staged.get("provider_label") if isinstance(staged, dict) else None,
                        is_cloned=bool(staged.get("is_cloned", False)) if isinstance(staged, dict) else False,
                    )
                except Exception:
                    pass
            return dict(self._last_staged)
        except Exception as exc:
            logger.error("Voice output error: %s", exc)
            self._last_staged = {"status": "error", "error": str(exc)}
            return dict(self._last_staged)


    def stop(self) -> None:
        """Stop background listening loop and cleanly terminate thread."""
        self.listening = False
        self.state = "STANDBY"
        self._stop_event.set()
        with self._reply_enqueue_lock:
            self._delivery_stop.set()
            self._job_manager.cancel_active_jobs()
            while True:
                try:
                    self._reply_queue.get_nowait()
                except queue.Empty:
                    break
                self._reply_queue.task_done()

        try:
            from apps.voice.wake_word_engine import wake_word_engine
            wake_word_engine.stop()
        except Exception as exc:
            logger.debug("WakeWordEngine stop notice: %s", exc)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

        logger.info("VoiceService stopped.")


# Module-level singleton instance for API routes and imports
voice_service = VoiceService()
