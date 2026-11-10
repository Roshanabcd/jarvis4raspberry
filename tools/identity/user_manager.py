"""
JARVIS OS — Identity and User Management Subsystem.
Implements Role-Based Access Control (ADMIN, USER, GUEST), secure credential
hashing (PBKDF2-HMAC-SHA256), rate-limiting, and local biometric face recognition.

Features:
- Deliberate first-time administrator enrollment with PIN & face confirmation
- Biometric storage isolated under private data/identity directory (0700 permissions)
- Face embeddings kept separate from ordinary photos
- Rate-limited PIN verification (60s lockout after 5 failed attempts)
- Multi-user support with role enforcement: ADMIN, USER, GUEST
- Zero cloud transmission: 100% private local identity verification
"""

import datetime
import hashlib
import json
import logging
import os
import secrets
import stat
import threading
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.identity.face_engine import face_engine, COSINE_SIMILARITY_THRESHOLD

logger = logging.getLogger("JARVIS.Identity.UserManager")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IDENTITY_DIR = PROJECT_ROOT / "data" / "identity"
USERS_FILE = IDENTITY_DIR / "users.json"
ENROLLMENT_PHOTOS_DIR = IDENTITY_DIR / "biometrics"

# Ensure directory exists with private permissions (rwx------)
IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
ENROLLMENT_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
try:
    os.chmod(IDENTITY_DIR, stat.S_IRWXU)
    os.chmod(ENROLLMENT_PHOTOS_DIR, stat.S_IRWXU)
except Exception:
    pass


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"


class UserManager:
    """Manages enrolled user accounts, PIN security, roles, and facial identification."""

    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._lock = threading.RLock()
        self._users: Dict[str, Dict[str, Any]] = {}
        self._failed_pin_attempts: int = 0
        self._lockout_until: float = 0.0
        self._max_pin_attempts = 5
        self._lockout_duration_s = 60.0

        self._load_users()
        self._initialized = True

    def _load_users(self) -> None:
        """Load enrolled identities from secure disk storage."""
        with self._lock:
            if USERS_FILE.exists():
                try:
                    data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
                    self._users = data.get("users", {})
                    logger.info("Loaded %d enrolled users from identity store.", len(self._users))
                except Exception as e:
                    logger.error("Failed to parse identity store %s: %s", USERS_FILE, e)
                    self._users = {}
            else:
                self._users = {}
                self._save_users()

    def _save_users(self) -> None:
        """Write enrolled identities to secure disk storage with 0600 permissions."""
        with self._lock:
            payload = {
                "version": "1.0",
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "users": self._users,
            }
            USERS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            try:
                os.chmod(USERS_FILE, stat.S_IRUSR | stat.S_IWUSR)
            except Exception:
                pass

    def is_admin_enrolled(self) -> bool:
        """Check if an administrator account is registered."""
        with self._lock:
            return any(u.get("role") == UserRole.ADMIN.value for u in self._users.values())

    def get_admin_user(self) -> Optional[Dict[str, Any]]:
        """Return admin user metadata or None."""
        with self._lock:
            for u in self._users.values():
                if u.get("role") == UserRole.ADMIN.value:
                    return self._redact_user(u)
            return None

    def _hash_pin(self, pin: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash PIN using PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        salt_bytes = bytes.fromhex(salt)
        derived = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt_bytes, 100000)
        return derived.hex(), salt

    def _verify_pin_hash(self, pin: str, stored_hash: str, salt: str) -> bool:
        """Constant-time comparison of PIN hash."""
        derived_hash, _ = self._hash_pin(pin, salt)
        return secrets.compare_digest(derived_hash, stored_hash)

    def is_pin_locked(self) -> Tuple[bool, float]:
        """Check if PIN verification is currently rate-limited."""
        now = time.time()
        if now < self._lockout_until:
            remaining = round(self._lockout_until - now, 1)
            return True, remaining
        return False, 0.0

    def verify_admin_pin(self, pin: str) -> Tuple[bool, str]:
        """Verify administrator PIN with brute-force rate-limiting."""
        locked, rem = self.is_pin_locked()
        if locked:
            return False, f"Too many failed PIN attempts. Locked out for {rem} more seconds."

        with self._lock:
            admin = None
            for u in self._users.values():
                if u.get("role") == UserRole.ADMIN.value:
                    admin = u
                    break

            if not admin:
                self._failed_pin_attempts += 1
                if self._failed_pin_attempts >= self._max_pin_attempts:
                    self._lockout_until = time.time() + self._lockout_duration_s
                    return False, f"Too many failed PIN attempts. Locked out for {self._lockout_duration_s}s."
                return False, "No administrator is currently enrolled."

            salt = admin.get("pin_salt", "")
            stored_hash = admin.get("pin_hash", "")

            if self._verify_pin_hash(pin, stored_hash, salt):
                self._failed_pin_attempts = 0
                return True, "Administrator authentication verified."
            else:
                self._failed_pin_attempts += 1
                if self._failed_pin_attempts >= self._max_pin_attempts:
                    self._lockout_until = time.time() + self._lockout_duration_s
                    logger.warning("Administrator PIN rate-limit lockout triggered for %ds.", self._lockout_duration_s)
                    return False, f"Incorrect PIN. 5 failed attempts reached; locked out for {self._lockout_duration_s}s."
                remaining_tries = self._max_pin_attempts - self._failed_pin_attempts
                return False, f"Incorrect PIN. {remaining_tries} attempts remaining before lockout."

    def enroll_admin(
        self,
        display_name: str,
        pin: str,
        photo_path: str,
        confirmed: bool = False,
    ) -> Dict[str, Any]:
        """
        Enroll the primary administrator.
        Requires valid photo with detectable face, non-empty PIN, and explicit confirmation.
        """
        with self._lock:
            if self.is_admin_enrolled():
                return {
                    "success": False,
                    "error": "Administrator is already enrolled. Face enrollment cannot overwrite existing admin.",
                }

            if not confirmed:
                return {
                    "success": False,
                    "error": "Administrator enrollment requires explicit user confirmation.",
                }

            if not display_name or not display_name.strip():
                return {"success": False, "error": "Display name cannot be empty."}

            if not pin or len(pin) < 4:
                return {"success": False, "error": "Admin PIN must be at least 4 digits."}

            if not os.path.exists(photo_path):
                return {"success": False, "error": f"Photo file not found: {photo_path}"}

            # 1. Detect face and extract embedding
            faces = face_engine.detect_faces(photo_path)
            if not faces:
                return {
                    "success": False,
                    "error": "No face was detected in the captured photo. Please ensure good lighting and face the camera directly.",
                }
            if len(faces) > 1:
                return {
                    "success": False,
                    "error": f"Multiple faces ({len(faces)}) detected. Administrator enrollment requires exactly one person in the frame.",
                }

            embedding = face_engine.extract_embedding(photo_path, faces[0])
            if not embedding:
                return {"success": False, "error": "Failed to extract facial recognition embedding from photo."}

            # 2. Hash PIN securely
            pin_hash, salt = self._hash_pin(pin)

            # 3. Store isolated biometric face template under private identity directory
            user_id = f"admin_{uuid.uuid4().hex[:8]}"
            user_doc = {
                "user_id": user_id,
                "display_name": display_name.strip(),
                "role": UserRole.ADMIN.value,
                "pin_hash": pin_hash,
                "pin_salt": salt,
                "face_embedding": embedding,
                "face_confidence": faces[0]["confidence"],
                "enrolled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "last_seen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

            self._users[user_id] = user_doc
            self._save_users()
            logger.info("✓ Administrator enrolled successfully: %s (ID: %s)", display_name, user_id)

            return {
                "success": True,
                "user_id": user_id,
                "display_name": display_name.strip(),
                "role": UserRole.ADMIN.value,
                "face_confidence": faces[0]["confidence"],
                "message": f"Administrator '{display_name.strip()}' enrolled successfully with role ADMIN.",
            }

    def enroll_user(
        self,
        display_name: str,
        role: str,
        photo_path: str,
        admin_pin: str,
    ) -> Dict[str, Any]:
        """Enroll a standard user. Requires admin PIN verification and user consent."""
        pin_ok, pin_msg = self.verify_admin_pin(admin_pin)
        if not pin_ok:
            return {"success": False, "error": f"Admin authorization failed: {pin_msg}"}

        target_role = UserRole.USER.value if role.upper() == UserRole.USER.value else UserRole.GUEST.value

        with self._lock:
            if not display_name or not display_name.strip():
                return {"success": False, "error": "Display name cannot be empty."}

            if not os.path.exists(photo_path):
                return {"success": False, "error": f"Photo file not found: {photo_path}"}

            faces = face_engine.detect_faces(photo_path)
            if not faces:
                return {"success": False, "error": "No face detected in the enrollment photo."}

            embedding = face_engine.extract_embedding(photo_path, faces[0])
            if not embedding:
                return {"success": False, "error": "Failed to extract facial embedding."}

            user_id = f"user_{uuid.uuid4().hex[:8]}"
            user_doc = {
                "user_id": user_id,
                "display_name": display_name.strip(),
                "role": target_role,
                "face_embedding": embedding,
                "face_confidence": faces[0]["confidence"],
                "enrolled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "last_seen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

            self._users[user_id] = user_doc
            self._save_users()
            logger.info("✓ Enrolled %s: %s (ID: %s)", target_role, display_name, user_id)

            return {
                "success": True,
                "user_id": user_id,
                "display_name": display_name.strip(),
                "role": target_role,
                "message": f"User '{display_name.strip()}' enrolled successfully with role {target_role}.",
            }

    def identify_user_from_image(
        self,
        photo_path: str,
    ) -> Dict[str, Any]:
        """
        Identify active user from camera image.
        Returns matched user profile or GUEST if unknown.
        """
        if not os.path.exists(photo_path):
            return {
                "identified": False,
                "role": UserRole.GUEST.value,
                "display_name": "Guest",
                "reason": "Image not found",
            }

        faces = face_engine.detect_faces(photo_path)
        if not faces:
            return {
                "identified": False,
                "role": UserRole.GUEST.value,
                "display_name": "Guest",
                "reason": "No face detected in frame",
            }

        # Select primary face
        primary_face = max(faces, key=lambda f: f["confidence"])
        query_embedding = face_engine.extract_embedding(photo_path, primary_face)
        if not query_embedding:
            return {
                "identified": False,
                "role": UserRole.GUEST.value,
                "display_name": "Guest",
                "reason": "Could not extract face embedding",
            }

        with self._lock:
            best_match: Optional[Dict[str, Any]] = None
            best_score: float = -1.0

            for u in self._users.values():
                ref_emb = u.get("face_embedding")
                if not ref_emb:
                    continue
                is_match, score = face_engine.compare_embeddings(query_embedding, ref_emb)
                if is_match and score > best_score:
                    best_score = score
                    best_match = u

            if best_match and best_score >= COSINE_SIMILARITY_THRESHOLD:
                # Update last seen timestamp
                best_match["last_seen_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                self._save_users()

                logger.info("✓ Identified user: %s (Role: %s, Score: %.3f)",
                            best_match["display_name"], best_match["role"], best_score)
                return {
                    "identified": True,
                    "user_id": best_match["user_id"],
                    "display_name": best_match["display_name"],
                    "role": best_match["role"],
                    "similarity_score": round(best_score, 4),
                    "confidence": primary_face["confidence"],
                }
            else:
                logger.info("Unrecognized face in frame (best similarity: %.3f < %.3f). Assigned GUEST.",
                            best_score, COSINE_SIMILARITY_THRESHOLD)
                return {
                    "identified": False,
                    "role": UserRole.GUEST.value,
                    "display_name": "Guest",
                    "best_score": round(max(0.0, best_score), 4),
                    "reason": "Unknown face (below similarity threshold)",
                }

    def list_users(self) -> List[Dict[str, Any]]:
        """List all registered users with biometric and PIN secrets redacted."""
        with self._lock:
            return [self._redact_user(u) for u in self._users.values()]

    def delete_user(self, user_id: str, admin_pin: str) -> Dict[str, Any]:
        """Delete user account with administrator authorization."""
        pin_ok, pin_msg = self.verify_admin_pin(admin_pin)
        if not pin_ok:
            return {"success": False, "error": f"Admin authorization failed: {pin_msg}"}

        with self._lock:
            if user_id not in self._users:
                return {"success": False, "error": "User ID not found"}

            target = self._users[user_id]
            # Prevent removing last admin unless explicitly resetting
            if target.get("role") == UserRole.ADMIN.value:
                admin_count = sum(1 for u in self._users.values() if u.get("role") == UserRole.ADMIN.value)
                if admin_count <= 1:
                    return {"success": False, "error": "Cannot delete the sole administrator account."}

            name = target.get("display_name", user_id)
            del self._users[user_id]
            self._save_users()
            logger.info("Deleted user profile: %s (%s)", name, user_id)
            return {"success": True, "message": f"User '{name}' removed successfully."}

    def _redact_user(self, u: Dict[str, Any]) -> Dict[str, Any]:
        """Create sanitized copy of user record excluding PIN and face embeddings."""
        return {
            "user_id": u.get("user_id"),
            "display_name": u.get("display_name"),
            "role": u.get("role"),
            "has_face_enrolled": bool(u.get("face_embedding")),
            "face_confidence": u.get("face_confidence"),
            "enrolled_at": u.get("enrolled_at"),
            "last_seen_at": u.get("last_seen_at"),
        }


user_manager = UserManager()
