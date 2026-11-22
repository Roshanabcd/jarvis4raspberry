"""
Task Completion Announcer for JARVIS OS.

Generates concise, natural 1-2 sentence spoken announcements for:
- Developer Hub gated actions (/api/developer/execute)
- Background Tasks (apps/tasks/background.py / tjob_*)
- Orchestrator tasks (/api/developer/tasks/{task_id}/run)

Routes all announcements through the single-owner voice preemption pipeline
(voice_service.enqueue_response with preempt=True) to guarantee zero overlapping voices.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS.Voice.TaskAnnouncer")

_SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|\bkey\b|token|password|secret|pin)(\s*[=:]\s*)[^\s,;]+")


def clean_spoken_text(text: str) -> str:
    """Strip markdown, URLs, code blocks, JSON, and technical noise for clean speech."""
    if not text:
        return ""
    # Redact any secrets
    t = _SECRET_PATTERN.sub("", str(text))
    # Remove code blocks
    t = re.sub(r"```[\s\S]*?```", "", t)
    # Remove inline backticks
    t = re.sub(r"`([^`]+)`", r"\1", t)
    # Remove markdown links [text](url) -> text
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    # Remove raw URLs
    t = re.sub(r"https?://\S+", "", t)
    # Remove raw json characters
    t = re.sub(r"[{}\[\]\"]", "", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def make_completion_summary(
    status: str,
    action_or_name: str = "task",
    output_file: Optional[str] = None,
    output_summary: Optional[str] = None,
    failover_trace: Optional[List[Dict[str, Any]]] = None,
    error: Optional[str] = None,
) -> str:
    """Generate a crisp, conversational 1-2 sentence completion announcement."""
    st = str(status).lower()

    # 1. Success cases
    if st in ("ok", "succeeded", "success", "completed"):
        if output_file:
            fname = Path(output_file).name
            parent = Path(output_file).parent.name
            target_str = f"{parent} as {fname}" if parent and parent not in (".", "") else fname
            return f"Task complete. I generated the image and saved it to {target_str}."

        if output_summary:
            clean = clean_spoken_text(output_summary)
            # Take the first complete sentence
            sentences = [s.strip() for s in clean.split(".") if s.strip()]
            if sentences and len(sentences[0]) > 5:
                first = sentences[0]
                if len(first) > 120:
                    first = first[:117] + "..."
                return f"Task complete. {first}."

        return f"{action_or_name.replace('_', ' ').capitalize()} completed successfully."

    # 2. Quota / Rate-limit / Failover failure cases
    is_quota = (
        st in ("quota_exhausted", "resource_exhausted")
        or (error and bool(re.search(r"(?i)(429|quota|resource_exhausted|rate\s*limit)", error)))
    )
    if is_quota:
        tried_names: List[str] = []
        if failover_trace:
            for item in failover_trace:
                name = item.get("cli") or item.get("provider") or item.get("step") or item.get("agent")
                if name:
                    raw_n = str(name).lower()
                    if "antigravity" in raw_n or raw_n == "agy":
                        disp = "Antigravity"
                    elif "freellmapi" in raw_n:
                        disp = "FreeLLMAPI"
                    elif "claude" in raw_n:
                        disp = "Claude"
                    else:
                        disp = str(name).replace("_", " ").title()
                    if disp not in tried_names:
                        tried_names.append(disp)
        if tried_names:
            tried_str = " after trying " + " and ".join(tried_names)
        else:
            tried_str = ""
        return f"The task failed{tried_str} because the model quota is exhausted."

    # 3. Timeout cases
    if st == "timeout" or (error and "timed out" in error.lower()):
        return "The task timed out before completing."

    # 4. Cancellation
    if st == "cancelled":
        return f"{action_or_name.replace('_', ' ').capitalize()} was cancelled."

    # 5. Generic error
    err_clean = clean_spoken_text(error or "Execution error")
    err_sentences = [s.strip() for s in err_clean.split(".") if s.strip()]
    first_err = err_sentences[0] if err_sentences else "An error occurred"
    if len(first_err) > 90:
        first_err = first_err[:87] + "..."
    return f"The task failed: {first_err}."


def announce_task_completion(
    status: str,
    action_or_name: str = "task",
    output_file: Optional[str] = None,
    output_summary: Optional[str] = None,
    failover_trace: Optional[List[Dict[str, Any]]] = None,
    error: Optional[str] = None,
    auto_speak: Optional[bool] = None,
) -> Optional[str]:
    """Build and dispatch spoken completion phrase via the single-owner TTS pipeline."""
    try:
        from config.config_manager import config
        if auto_speak is None:
            auto_speak = bool(config.get("voice", {}).get("auto_speak", True))
    except Exception:
        if auto_speak is None:
            auto_speak = True

    if not auto_speak:
        logger.debug("Auto-speak is disabled; skipping completion announcement.")
        return None

    phrase = make_completion_summary(
        status=status,
        action_or_name=action_or_name,
        output_file=output_file,
        output_summary=output_summary,
        failover_trace=failover_trace,
        error=error,
    )

    if not phrase:
        return None

    logger.info("Announcing task completion aloud: '%s'", phrase)

    try:
        from apps.voice.service import voice_service
        # Enqueue with preempt=True: advances generation, cancels any stale playback, and speaks this phrase
        voice_service.enqueue_response(phrase, broadcast=True, preempt=True)
    except Exception as exc:
        logger.warning("Failed to enqueue spoken announcement: %s", exc)

    return phrase
