"""Real-Time Conversational AI Engine with viseme timeline, interruption & error recovery."""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from modules.module_20_realtime_conversational_ai.backend.adapters.provider_adapters import (
    PERSONA_PROFILES,
    ConversationalProviderAdapter,
    OpenAICompatibleProvider,
    SimulatedLocalProvider,
)
from modules.module_20_realtime_conversational_ai.backend.app.config import ConversationalConfig
from modules.module_20_realtime_conversational_ai.backend.models.database import ConversationalDB, utc_now_iso


def generate_approximate_visemes(text: str) -> List[Dict[str, Any]]:
    """Generate an approximate syllable/vowel viseme timeline for avatar mouth animation.

    Clearly distinguished from phoneme-accurate audio forced alignment.
    """
    cues: List[Dict[str, Any]] = []
    t_ms = 0
    for word in re.findall(r"[A-Za-z0-9']+", text):
        low = word.lower()
        if any(ch in low for ch in ("a", "o")):
            viseme, openness = "AA", 0.85
        elif any(ch in low for ch in ("e", "i")):
            viseme, openness = "EE", 0.58
        elif "u" in low:
            viseme, openness = "OO", 0.65
        elif low[:1] in ("m", "b", "p"):
            viseme, openness = "MBP", 0.15
        else:
            viseme, openness = "MID", 0.42
        cues.append({"time_ms": t_ms, "viseme": viseme, "openness": openness, "word": word})
        t_ms += max(110, min(340, len(word) * 48))
    cues.append({"time_ms": t_ms, "viseme": "REST", "openness": 0.05, "word": ""})
    return cues


def infer_facial_state(text: str, fallback_used: bool = False) -> str:
    if fallback_used:
        return "alert"
    low = text.lower()
    if any(w in low for w in ("hello", "welcome", "great", "ready", "operational")):
        return "happy"
    if any(w in low for w in ("error", "warning", "failed", "cannot")):
        return "alert"
    return "speaking"


class ConversationalEngine:
    def __init__(
        self,
        config: Optional[ConversationalConfig] = None,
        db: Optional[ConversationalDB] = None,
    ) -> None:
        self.config = config or ConversationalConfig.from_env()
        self.config.ensure_db_dir()
        self.db = db or ConversationalDB(self.config.db_path)
        self._fallback_provider = SimulatedLocalProvider()
        self._active_interrupts: Dict[str, asyncio.Event] = {}
        self._started_at = time.monotonic()

    def _get_primary_provider(self) -> ConversationalProviderAdapter:
        if self.config.provider in ("openai_compatible", "ollama") and self.config.provider_url:
            return OpenAICompatibleProvider(self.config.provider_url, self.config.provider_api_key)
        return self._fallback_provider

    def create_session(self, title: str, persona: str = "aria", system_prompt: Optional[str] = None) -> Dict[str, Any]:
        now = utc_now_iso()
        profile = PERSONA_PROFILES.get(persona, PERSONA_PROFILES["aria"])
        default_prompt = system_prompt or f"You are {profile['name']}, a JARVIS OS conversational assistant."
        return self.db.create_session(
            {
                "session_id": f"ses_{uuid.uuid4().hex[:10]}",
                "title": title,
                "persona": profile["id"],
                "system_prompt": default_prompt,
                "created_at": now,
                "updated_at": now,
            }
        )

    def ensure_session(self, session_id: Optional[str], persona: str = "aria") -> Dict[str, Any]:
        if session_id:
            existing = self.db.get_session(session_id)
            if existing:
                return existing
        return self.create_session("JARVIS Voice Session", persona=persona)

    def _build_context(self, session: Dict[str, Any]) -> List[Dict[str, str]]:
        history = self.db.list_messages(session["session_id"], limit=200)
        window = history[-self.config.context_window :]
        ctx: List[Dict[str, str]] = []
        if session.get("system_prompt"):
            ctx.append({"role": "system", "content": session["system_prompt"]})
        for m in window:
            ctx.append({"role": m["role"], "content": m["content"]})
        return ctx

    def interrupt_session(self, session_id: str) -> Dict[str, Any]:
        ev = self._active_interrupts.get(session_id)
        if ev:
            ev.set()
            return {"session_id": session_id, "interrupted": True}
        return {"session_id": session_id, "interrupted": False, "note": "No active generation stream for session"}

    async def stream_turn(
        self,
        session_id: Optional[str],
        user_content: str,
        persona: str = "aria",
        simulate_provider_error: bool = False,
    ) -> AsyncIterator[Dict[str, Any]]:
        session = self.ensure_session(session_id, persona=persona)
        sid = session["session_id"]

        user_msg = self.db.add_message(
            {
                "message_id": f"msg_{uuid.uuid4().hex[:10]}",
                "session_id": sid,
                "role": "user",
                "content": user_content,
                "persona": persona,
                "provider": "user",
                "facial_state": "listening",
            }
        )
        yield {"event": "turn.started", "session_id": sid, "user_message": user_msg, "facial_state": "thinking"}

        interrupt_ev = asyncio.Event()
        self._active_interrupts[sid] = interrupt_ev
        context = self._build_context(session)
        primary = self._get_primary_provider()

        tokens: List[str] = []
        fallback_used = False
        recovery_error: Optional[str] = None
        interrupted = False

        try:
            if simulate_provider_error:
                raise RuntimeError("Simulated primary AI provider outage")
            async for tok in primary.stream_reply(context, persona=persona, model=self.config.provider_model):
                if interrupt_ev.is_set():
                    interrupted = True
                    break
                tokens.append(tok)
                yield {"event": "turn.token", "session_id": sid, "token": tok, "facial_state": "speaking"}
        except Exception as exc:
            fallback_used = True
            recovery_error = str(exc)
            yield {
                "event": "provider.fallback",
                "session_id": sid,
                "error": recovery_error,
                "fallback_provider": self._fallback_provider.provider_name,
            }
            async for tok in self._fallback_provider.stream_reply(context, persona=persona, model="fallback-sim"):
                if interrupt_ev.is_set():
                    interrupted = True
                    break
                tokens.append(tok)
                yield {"event": "turn.token", "session_id": sid, "token": tok, "facial_state": "speaking"}
        finally:
            self._active_interrupts.pop(sid, None)

        full_text = "".join(tokens).strip() or "(Interrupted before response text)"
        visemes = generate_approximate_visemes(full_text)
        facial_state = "interrupted" if interrupted else infer_facial_state(full_text, fallback_used=fallback_used)

        assistant_msg = self.db.add_message(
            {
                "message_id": f"msg_{uuid.uuid4().hex[:10]}",
                "session_id": sid,
                "role": "assistant",
                "content": full_text,
                "persona": persona,
                "provider": self._fallback_provider.provider_name if fallback_used else primary.provider_name,
                "fallback_used": fallback_used,
                "interrupted": interrupted,
                "facial_state": facial_state,
                "metadata": {
                    "lip_sync_mode": "approximate_syllable_viseme",
                    "recovery_error": recovery_error,
                    "viseme_count": len(visemes),
                },
            }
        )

        yield {
            "event": "turn.interrupted" if interrupted else "turn.completed",
            "session_id": sid,
            "assistant_message": assistant_msg,
            "visemes": visemes,
            "lip_sync_mode": "approximate_syllable_viseme",
            "facial_state": facial_state,
            "fallback_used": fallback_used,
            "recovery_error": recovery_error,
        }

    async def complete_turn(
        self,
        session_id: Optional[str],
        user_content: str,
        persona: str = "aria",
        simulate_provider_error: bool = False,
    ) -> Dict[str, Any]:
        final_evt: Dict[str, Any] = {}
        async for evt in self.stream_turn(
            session_id=session_id,
            user_content=user_content,
            persona=persona,
            simulate_provider_error=simulate_provider_error,
        ):
            if evt["event"] in ("turn.completed", "turn.interrupted"):
                final_evt = evt
        return final_evt

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider": self.config.provider,
            "provider_model": self.config.provider_model,
            "simulated": self._get_primary_provider().is_simulated,
            "lip_sync_mode": "approximate_syllable_viseme",
            "context_window": self.config.context_window,
            "sessions_count": len(self.db.list_sessions(limit=200)),
            "personas": list(PERSONA_PROFILES.values()),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
