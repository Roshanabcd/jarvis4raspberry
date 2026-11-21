"""
JARVIS OS — Voice Session & Identity Manager.
Coordinates active voice conversation sessions with biometric face recognition,
RBAC role enforcement (ADMIN, USER, GUEST), session expiration, and anti-escalation security.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel, Field

from tools.identity.user_manager import UserRole, user_manager
from tools.vision.camera_manager import camera_manager

logger = logging.getLogger("JARVIS.Voice.SessionManager")


class VoiceSession(BaseModel):
    """Authenticated state for a voice interaction turn."""
    session_id: str = Field(default_factory=lambda: f"vsession_{uuid.uuid4().hex[:10]}")
    user_id: str = "guest"
    display_name: str = "Guest"
    role: str = UserRole.GUEST.value
    confidence: float = 0.0
    source: str = "default_guest"
    created_at: float = Field(default_factory=time.time)
    expires_at: float = Field(default_factory=lambda: time.time() + 300.0)  # 5 min default
    is_authenticated: bool = False
    is_admin_elevated: bool = False

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def refresh(self, duration_s: float = 300.0) -> None:
        self.expires_at = time.time() + duration_s

    def authorization_role(self) -> str:
        """Return the role usable for tool authorization in this voice turn.

        Face recognition may identify an administrator, but recognition alone must
        never authorize administrative actions.  An administrator retains normal
        USER capabilities until a separate PIN verification elevates this session.
        """
        if self.role == UserRole.ADMIN.value and not self.is_admin_elevated:
            return UserRole.USER.value
        return self.role


class VoiceSessionManager:
    """Singleton managing active voice session state and biometric synchronization."""

    _instance: Optional[VoiceSessionManager] = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, session_ttl_s: float = 300.0):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.session_ttl_s = session_ttl_s
        self._current_session: VoiceSession = VoiceSession()
        self._initialized = True
        logger.info("VoiceSessionManager initialized (TTL: %.1fs)", self.session_ttl_s)

    def get_active_session(self) -> VoiceSession:
        """Return active voice session, creating a safe GUEST session if expired."""
        with self._lock:
            if self._current_session.is_expired():
                logger.info("Voice session %s expired. Resetting to GUEST.", self._current_session.session_id)
                self._current_session = VoiceSession()
            return self._current_session

    def create_session(
        self,
        user_id: str,
        display_name: str,
        role: str,
        confidence: float = 1.0,
        source: str = "manual",
        is_authenticated: bool = True,
        is_admin_elevated: bool = False,
    ) -> VoiceSession:
        """Explicitly create an authenticated voice session."""
        with self._lock:
            role_val = role.upper() if role.upper() in (UserRole.ADMIN.value, UserRole.USER.value, UserRole.GUEST.value) else UserRole.GUEST.value
            self._current_session = VoiceSession(
                user_id=user_id,
                display_name=display_name,
                role=role_val,
                confidence=confidence,
                source=source,
                created_at=time.time(),
                expires_at=time.time() + self.session_ttl_s,
                is_authenticated=is_authenticated,
                # A biometric match establishes identity, not administrative
                # authority.  Only verify_admin_pin() can set this flag.
                is_admin_elevated=bool(is_admin_elevated),
            )
            logger.info("Created voice session %s for '%s' (Role: %s, Source: %s)",
                        self._current_session.session_id, display_name, role_val, source)
            return self._current_session

    def set_session_ttl(self, ttl_s: float) -> None:
        with self._lock:
            self.session_ttl_s = ttl_s
            if not self._current_session.is_expired():
                self._current_session.refresh(ttl_s)
            logger.info("Session TTL updated to %.1fs", ttl_s)

    def extend_session(self, duration_s: Optional[float] = None) -> VoiceSession:
        with self._lock:
            ttl = duration_s if duration_s is not None else self.session_ttl_s
            self._current_session.refresh(ttl)
            logger.info("Session %s extended by %.1fs", self._current_session.session_id, ttl)
            return self._current_session

    def invalidate_session(self) -> VoiceSession:
        """Reset session to unauthenticated GUEST."""
        with self._lock:
            self._current_session = VoiceSession()
            logger.info("Voice session invalidated. Reverted to GUEST.")
            return self._current_session

    def identify_speaker_from_camera(self) -> Dict[str, Any]:
        """
        Capture current frame from the camera service on port 8082
        and perform facial recognition to establish the voice session.
        """
        with self._lock:
            current = self.get_active_session()
            if current.source == 'admin_pin' and current.is_admin_elevated:
                return {'success': True, 'identified': True, 'source': 'admin_pin',
                        'session': current.model_dump(),
                        'authorization_role': current.authorization_role(),
                        'reason': 'Using the active PIN-authenticated session; no camera capture requested'}
            # 1. Capture snapshot from existing camera manager
            # CameraManager deliberately proxies the already-running camera
            # service, so this does not create a second Picamera2 owner.
            cap_res = camera_manager.capture_photo()
            if not cap_res or not cap_res.get("success"):
                error = (cap_res or {}).get("error", "Camera capture unavailable")
                logger.warning("Camera snapshot failed for speaker identification: %s", error)
                return {
                    "success": False,
                    "session": self.get_active_session().model_dump(),
                    "reason": error,
                }

            photo_path = cap_res.get("image_path")
            if not photo_path:
                return {
                    "success": False,
                    "session": self.get_active_session().model_dump(),
                    "reason": "Missing image file path",
                }

            # 2. Run face recognition
            id_res = user_manager.identify_user_from_image(photo_path)
            if id_res.get("identified"):
                user_id = id_res.get("user_id", "user")
                name = id_res.get("display_name", "User")
                role = id_res.get("role", UserRole.USER.value)
                conf = id_res.get("confidence", 0.0)

                # Update session
                session = self.create_session(
                    user_id=user_id,
                    display_name=name,
                    role=role,
                    confidence=conf,
                    source="face_biometrics",
                    is_authenticated=True,
                    is_admin_elevated=False,  # ADMIN actions still require PIN
                )
                return {
                    "success": True,
                    "identified": True,
                    "user_id": user_id,
                    "display_name": name,
                    "role": role,
                    "confidence": conf,
                    "session": session.model_dump(),
                    "authorization_role": session.authorization_role(),
                }
            else:
                # Unrecognized face -> safe GUEST session
                session = self.create_session(
                    user_id="guest",
                    display_name="Guest",
                    role=UserRole.GUEST.value,
                    confidence=0.0,
                    source="unrecognized_face",
                    is_authenticated=False,
                )
                return {
                    "success": True,
                    "identified": False,
                    "display_name": "Guest",
                    "role": UserRole.GUEST.value,
                    "reason": id_res.get("reason", "Face not recognized"),
                    "session": session.model_dump(),
                    "authorization_role": session.authorization_role(),
                }

    def verify_admin_pin(self, pin: str) -> Tuple[bool, str]:
        """
        Verify PIN for administrative escalation of the active voice session.
        Enforces 5-attempt rate-limiting lockout.
        """
        with self._lock:
            is_valid, msg = user_manager.verify_admin_pin(pin)
            if is_valid:
                admin_user = user_manager.get_admin_user() or {}
                self._current_session.is_admin_elevated = True
                self._current_session.is_authenticated = True
                self._current_session.source = 'admin_pin'
                self._current_session.role = UserRole.ADMIN.value
                self._current_session.user_id = admin_user.get("user_id", "admin")
                self._current_session.display_name = admin_user.get("display_name", "Administrator")
                self._current_session.refresh(self.session_ttl_s)
                logger.info("Admin PIN verified. Voice session %s elevated to ADMIN.", self._current_session.session_id)
                return True, "Administrator privileges granted for voice session."
            else:
                logger.warning("Admin PIN verification failed: %s", msg)
                return False, msg


# Module-level singleton
voice_session_mgr = VoiceSessionManager()
