"""Exact, non-action conversational turns that need no remote inference."""
import re


def immediate_reply(message: str):
    text = re.sub(r"[!?.]+$", "", message.strip().lower()).strip()
    text = re.sub(r"\s+", " ", text)
    if text in {"hello", "hi", "hey", "hello jarvis", "hi jarvis", "hey jarvis", "jarvis", "namaste"}:
        return "Hello! I'm here. What would you like me to do?"
    if text in {"thanks", "thank you", "thank you jarvis"}:
        return "You're welcome."
    if text in {"are you there", "are you listening", "are you online"}:
        return "I'm here in chat. Voice listening status is shown in the Voice panel."
    return None
