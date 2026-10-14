"""
JARVIS Audit Logger
Production JSONL audit trail. Sanitizes secrets before writing.
Not a singleton — use the module-level `audit_logger` for production,
or create a new AuditLogger(log_path=...) instance for testing.
"""
import json
import logging
import os
import threading
import re
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional, Union

logger = logging.getLogger("JARVIS.Security.Audit")

# Patterns that indicate secret values to redact
_SECRET_PATTERNS = [
    re.compile(r'(sk-[A-Za-z0-9]{20,})', re.IGNORECASE),        # OpenAI keys
    re.compile(r'(Bearer\s+[A-Za-z0-9\-._~+/]{20,})', re.IGNORECASE),
    re.compile(r'(api[_-]?key\s*[=:]\s*[^\s,&"\']{8,})', re.IGNORECASE),
    re.compile(r'(password\s*[=:]\s*[^\s,&"\']{4,})', re.IGNORECASE),
    re.compile(r'(token\s*[=:]\s*[^\s,&"\']{8,})', re.IGNORECASE),
    re.compile(r'(secret\s*[=:]\s*[^\s,&"\']{4,})', re.IGNORECASE),
]


class AuditLogger:
    """
    Writes structured JSONL audit entries to a rotating log file.
    Sanitizes secrets in user_request field before persisting.
    Each instance owns its own file handler — safe for testing with custom paths.
    """

    def __init__(
        self,
        log_path: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ) -> None:
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._write_lock = threading.Lock()

        # Resolve log path
        if not log_path:
            env_path = os.environ.get("JARVIS_AUDIT_LOG")
            if env_path:
                log_path = env_path
            else:
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                log_path = os.path.join(project_root, "jarvis_audit.log")

        self.log_path = os.path.abspath(log_path)

        # Ensure directory exists
        _log_dir = os.path.dirname(self.log_path)
        if _log_dir:
            os.makedirs(_log_dir, exist_ok=True)

        # Each instance gets its own uniquely-named internal logger
        self._writer = logging.getLogger(f"JARVIS_AUDIT_{id(self)}")
        self._writer.setLevel(logging.INFO)
        self._writer.propagate = False
        if not self._writer.handlers:
            handler = RotatingFileHandler(
                self.log_path,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._writer.addHandler(handler)

        logger.info("AuditLogger → %s", self.log_path)

    @staticmethod
    def sanitize(text: str) -> str:
        """Replace secret patterns with [REDACTED]."""
        if not text:
            return text
        for pattern in _SECRET_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text

    def log_event(
        self,
        service: str,
        event: str,
        tool: Optional[str] = None,
        status: str = "SUCCESS",
        risk_level: Union[int, str] = 0,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
        user_request: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Write one JSONL audit entry. Sanitizes user_request for secrets.
        Never logs raw API keys, tokens, or passwords.
        """
        try:
            sanitized_error   = self.sanitize(str(error)) if error is not None else None
            sanitized_request = self.sanitize(user_request) if user_request is not None else None

            record: Dict[str, Any] = {
                "timestamp":    datetime.now(timezone.utc).isoformat(),
                "service":      str(service),
                "event":        str(event),
                "tool":         str(tool) if tool is not None else None,
                "status":       str(status),
                "risk_level":   risk_level,
                "duration_ms":  round(float(duration_ms), 3),
                "error":        sanitized_error,
                "user_request": sanitized_request,
            }

            json_line = json.dumps(record, ensure_ascii=False)
            with self._write_lock:
                self._writer.info(json_line)
                # Flush immediately so test reads are reliable
                for h in self._writer.handlers:
                    h.flush()

            return record

        except Exception as exc:
            logger.error("Audit log write failure: %s", exc)
            return {
                "timestamp":    datetime.now(timezone.utc).isoformat(),
                "service":      str(service),
                "event":        str(event),
                "tool":         str(tool) if tool is not None else None,
                "status":       "AUDIT_ERROR",
                "risk_level":   risk_level,
                "duration_ms":  duration_ms,
                "error":        str(exc),
                "user_request": None,
            }

    @classmethod
    def get_instance(cls) -> "AuditLogger":
        """Return the module-level production singleton."""
        return audit_logger


# Production singleton — uses default log path
audit_logger = AuditLogger()
