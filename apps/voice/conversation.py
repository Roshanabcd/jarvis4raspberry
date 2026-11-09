"""Conversation Manager for JARVIS OS.

Manages turn-based dialogue sessions, context retrieval, session expiration,
and persistence to short-term memory.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from config.config_manager import config

logger = logging.getLogger("JARVIS-CONVERSATION")


class ConversationManager:
    """Manages conversational dialogue sessions and short-term memory integration."""

    def __init__(
        self,
        timeout_seconds: Optional[int] = None,
        storage_dir: Optional[str] = None,
    ):
        """Initialize the ConversationManager.

        Args:
            timeout_seconds: Dialogue session timeout in seconds. Defaults to config
                or 300 seconds.
            storage_dir: Path to directory for persisting sessions. Defaults to
                memory/short_term.
        """
        voice_cfg: Dict[str, Any] = config.get("voice", {})
        self.timeout_seconds: int = (
            timeout_seconds
            if timeout_seconds is not None
            else int(voice_cfg.get("conversation_timeout", 300))
        )

        # Base path for memory/short_term
        if storage_dir:
            self.storage_dir = storage_dir
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.storage_dir = os.path.join(base_dir, "memory", "short_term")

        os.makedirs(self.storage_dir, exist_ok=True)

        self.current_session_id: Optional[str] = None
        self.session_start_time: float = 0.0
        self.last_activity_time: float = 0.0
        self.turns: List[Dict[str, Any]] = []

        # Connect with short-term memory module if present
        self._short_term_memory = None
        try:
            from memory.short_term.conversation import ConversationMemory

            self._short_term_memory = ConversationMemory()
        except ImportError:
            logger.debug("ConversationMemory module not found; using internal list.")

        logger.info(
            "ConversationManager initialized (timeout=%ds, storage_dir=%s)",
            self.timeout_seconds,
            self.storage_dir,
        )

    def get_turns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent dialogue turns."""
        return self.turns[-limit:] if self.turns else []

    def is_session_active(self) -> bool:
        """Check if a session is currently active and within timeout bounds.

        Returns:
            bool: True if session exists and has not timed out.
        """
        if not self.current_session_id:
            return False

        if (time.time() - self.last_activity_time) > self.timeout_seconds:
            logger.info("Session %s expired due to timeout.", self.current_session_id)
            self.end_session()
            return False

        return True

    def start_session(self, session_id: Optional[str] = None) -> str:
        """Begin a new conversation session.

        If an existing session is active, it is ended and saved first.

        Args:
            session_id: Optional specific identifier. Defaults to generated UUID.

        Returns:
            str: Active session identifier.
        """
        if self.current_session_id:
            self.end_session()

        self.current_session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.session_start_time = time.time()
        self.last_activity_time = self.session_start_time
        self.turns = []

        logger.info("Started new dialogue session: %s", self.current_session_id)
        return self.current_session_id

    def add_turn(self, role: str, text: str) -> None:
        """Add a dialogue turn to the current session.

        If no active session exists or if it has timed out, starts a new one.

        Args:
            role: The participant role ('user', 'assistant', 'system').
            text: The spoken or transcribed text.
        """
        if not self.is_session_active():
            self.start_session()

        now = time.time()
        self.last_activity_time = now

        turn = {
            "role": role,
            "text": text,
            "timestamp": now,
        }
        self.turns.append(turn)

        # Update ConversationMemory if available
        if self._short_term_memory is not None:
            try:
                self._short_term_memory.add_message(role=role, content=text)
            except Exception as exc:
                logger.error("Failed to add message to ConversationMemory: %s", exc)

        logger.debug(
            "Turn added to session %s [%s]: %s",
            self.current_session_id,
            role,
            text[:60],
        )

    def get_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent dialogue turns for the active session.

        Args:
            limit: Maximum number of recent turns to return.

        Returns:
            List[Dict[str, Any]]: List of dialogue turns formatted as dicts.
        """
        if not self.is_session_active():
            return []

        return self.turns[-limit:]

    def end_session(self) -> None:
        """End the current conversation session and persist history to disk."""
        if not self.current_session_id:
            return

        session_id = self.current_session_id
        session_data = {
            "session_id": session_id,
            "start_time": self.session_start_time,
            "end_time": time.time(),
            "turn_count": len(self.turns),
            "turns": self.turns,
        }

        # Persist session to memory/short_term/<session_id>.json
        try:
            file_path = os.path.join(self.storage_dir, f"{session_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2)
            logger.info("Persisted session %s to %s", session_id, file_path)
        except Exception as exc:
            logger.error("Failed to persist session %s: %s", session_id, exc)

        self.current_session_id = None
        self.turns = []
        logger.info("Ended dialogue session: %s", session_id)
