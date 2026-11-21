"""Contextual Automatic Error Detection & Prompt-Injection Defense Engine (Module 43)."""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional

# Prompt-injection / untrusted screen command patterns (flagged & never executed)
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"--dangerously-skip-permissions", re.IGNORECASE),
    re.compile(r"\b(rm\s+-rf|curl\s+.*\|\s*sh|chmod\s+777)\b", re.IGNORECASE),
    re.compile(r"jarvis\s*,\s*(run|execute|delete|wipe|exfiltrate)", re.IGNORECASE),
]

# High-signal contextual error detectors (avoid matching harmless prose containing the word "error")
ERROR_RULES: List[Dict[str, Any]] = [
    {
        "title": "Python ModuleNotFoundError",
        "category": "programming",
        "severity": "high",
        "pattern": re.compile(r"(?:Traceback \(most recent call last\):[\s\S]{0,400})?ModuleNotFoundError:\s+No module named\s+['\"]?([A-Za-z0-9_.\-]+)['\"]?"),
        "likely_cause": "A required Python package or local module is not installed in the active virtual environment.",
        "suggested_action": "Verify the active virtual environment and install the missing dependency.",
        "confidence": 0.94,
        "repair_available": True,
    },
    {
        "title": "Python Runtime / Syntax / Assertion Exception",
        "category": "programming",
        "severity": "high",
        "pattern": re.compile(r"(?:Traceback \(most recent call last\):|File \".+\", line \d+)[\s\S]{0,600}\b(SyntaxError|TypeError|ValueError|AttributeError|NameError|ZeroDivisionError|AssertionError|ImportError|KeyError):\s*(.+)"),
        "likely_cause": "An unhandled Python exception or failing test assertion occurred during execution.",
        "suggested_action": "Inspect the failing file and line number, prepare a focused fix, and re-run tests.",
        "confidence": 0.92,
        "repair_available": True,
    },
    {
        "title": "Automated Test Suite Failure",
        "category": "programming",
        "severity": "high",
        "pattern": re.compile(r"\b(FAILED \(failures=\d+|FAILED \(errors=\d+|\d+ failed,\s*\d+ passed|AssertionError:)"),
        "likely_cause": "One or more automated tests failed against expected behavior.",
        "suggested_action": "Inspect the failing test output and authorize a targeted code repair.",
        "confidence": 0.91,
        "repair_available": True,
    },
    {
        "title": "Node.js / TypeScript / Vite Build Failure",
        "category": "programming",
        "severity": "high",
        "pattern": re.compile(r"(npm ERR!|error TS\d{4}:|SyntaxError: Unexpected token|Cannot find module ['\"][^'\"]+['\"])"),
        "likely_cause": "Frontend TypeScript compilation, module resolution, or npm build failed.",
        "suggested_action": "Review the TypeScript/npm error message and update the affected file or package.",
        "confidence": 0.89,
        "repair_available": True,
    },
    {
        "title": "System Resource / Service / Permission Failure",
        "category": "system",
        "severity": "critical",
        "pattern": re.compile(r"(No space left on device|Out of memory: Killed process|systemd\[1\]: .+ Failed|PermissionError: \[Errno 13\])", re.IGNORECASE),
        "likely_cause": "System-level disk exhaustion, OOM killer, service crash, or filesystem permission denial.",
        "suggested_action": "Check system telemetry (disk/RAM/services) before retrying.",
        "confidence": 0.90,
        "repair_available": False,
    },
    {
        "title": "Browser / Web Application Error",
        "category": "browser_app",
        "severity": "medium",
        "pattern": re.compile(r"(ERR_CONNECTION_REFUSED|502 Bad Gateway|500 Internal Server Error|Uncaught (TypeError|ReferenceError):)"),
        "likely_cause": "Backend service is unreachable or threw an unhandled server/client exception.",
        "suggested_action": "Verify the target service is running and inspect backend/console logs.",
        "confidence": 0.87,
        "repair_available": True,
    },
    {
        "title": "AI Provider / Coding Agent Failure",
        "category": "ai_agent",
        "severity": "medium",
        "pattern": re.compile(r"(429 Too Many Requests|RateLimitError|401 Unauthorized.*API key|APITimeoutError|model invocation failed)", re.IGNORECASE),
        "likely_cause": "AI provider rate limit, authentication failure, or request timeout.",
        "suggested_action": "Check provider quota, credentials, or switch to a fallback adapter.",
        "confidence": 0.88,
        "repair_available": False,
    },
]


class ErrorDetectionEngine:
    @staticmethod
    def detect_prompt_injection(screen_text: str) -> List[str]:
        """Flag suspicious instructions embedded in untrusted screen text."""
        hits: List[str] = []
        for pat in INJECTION_PATTERNS:
            m = pat.search(screen_text or "")
            if m:
                hits.append(m.group(0))
        return hits

    @staticmethod
    def sanitize_untrusted_text(screen_text: str) -> str:
        """Wrap screen text clearly as untrusted data and strip control chars."""
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", screen_text or "")
        return cleaned[:4000]

    def analyze_text(self, screen_text: str, source_app: str = "Unknown Application") -> Dict[str, Any]:
        sanitized = self.sanitize_untrusted_text(screen_text)
        injection_warnings = self.detect_prompt_injection(sanitized)
        detected: List[Dict[str, Any]] = []

        for rule in ERROR_RULES:
            m = rule["pattern"].search(sanitized)
            if m:
                snippet = m.group(0).strip()[:500]
                fp_raw = f"{rule['category']}|{rule['title']}|{source_app.lower()}|{snippet[:120].lower()}"
                fingerprint = hashlib.sha256(fp_raw.encode("utf-8")).hexdigest()[:16]
                detected.append(
                    {
                        "error_id": f"err_{uuid.uuid4().hex[:10]}",
                        "fingerprint": fingerprint,
                        "title": rule["title"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "status": "new",
                        "source_app": source_app,
                        "extracted_text": snippet,
                        "likely_cause": rule["likely_cause"],
                        "confidence": rule["confidence"],
                        "suggested_action": rule["suggested_action"],
                        "repair_available": rule["repair_available"],
                    }
                )

        return {
            "errors": detected,
            "prompt_injection_detected": len(injection_warnings) > 0,
            "injection_warnings": injection_warnings,
            "treated_as_untrusted_data": True,
        }
