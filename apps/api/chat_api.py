"""
JARVIS Chat API — Real AI brain with streaming SSE, tool calling, and multi-provider switching.
"""
import json
import logging
from typing import Any, Dict, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from apps.api.admin_action_policy import require_admin_action
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("JARVIS.API.Chat")
chat_router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    session_id: Optional[str] = None
    use_tools: bool = True
    provider: Optional[str] = None
    model: Optional[str] = None
    allow_fallback: bool = False
    max_provider_retries: int = Field(default=1, ge=0, le=3)
    speak: bool = False
    audio_output: Literal["browser", "system"] = "system"


class ModelSwitchRequest(BaseModel):
    provider: str = Field(..., min_length=1)
    model: Optional[str] = None


class ProviderTestRequest(BaseModel):
    provider: Literal['openai', 'gemini', 'anthropic', 'nvidia', 'openrouter', 'groq', 'together']


class ChatCancelRequest(BaseModel):
    request_id: str


@chat_router.post("/cancel")
def cancel_chat_endpoint(req: ChatCancelRequest):
    """Cancel a running AI chat request."""
    from ai.brain import get_brain
    brain = get_brain()
    ok = brain.cancel_request(req.request_id)
    return {"status": "ok" if ok else "not_found", "request_id": req.request_id}


@chat_router.post("/cancel/{request_id}")
def cancel_chat_by_id_endpoint(request_id: str):
    """Cancel a running AI chat request by URL parameter."""
    from ai.brain import get_brain
    brain = get_brain()
    ok = brain.cancel_request(request_id)
    return {"status": "ok" if ok else "not_found", "request_id": request_id}


@chat_router.post('/providers/test')
def test_provider_endpoint(req: ProviderTestRequest, _: None = Depends(require_admin_action)):
    """Send one synthetic prompt only after an explicit authenticated test action."""
    from ai.brain import get_brain
    from ai.providers.diagnostics import probe_provider
    provider = next((p for p in get_brain()._providers if p.name == req.provider), None)
    if provider is None:
        raise HTTPException(status_code=404, detail='Provider is not registered')
    return probe_provider(provider)


@chat_router.post("")
def chat_endpoint(req: ChatRequest) -> Dict[str, Any]:
    """Process a chat message through the JARVIS AI brain synchronously."""
    if req.speak:
        try:
            from apps.voice.service import voice_service
            voice_service.stop_playback()
        except Exception:
            pass
        try:
            from apps.voice.speech_manager import speech_manager
            speech_manager.stop()
        except Exception:
            pass

    from ai.brain import get_brain
    brain = get_brain()
    result = brain.chat(
        user_message=req.message,
        use_tools=req.use_tools,
        session_id=req.session_id,
        provider_name=req.provider,
        model_name=req.model,
        allow_fallback=req.allow_fallback,
        max_provider_retries=req.max_provider_retries,
    )

    # Text-first: only synthesize speech if explicitly requested (speak=True)
    resp_text = result.get("response", "")
    if req.speak and resp_text and not result.get('error') and result.get('status') not in {'failed', 'cancelled'}:
        try:
            from apps.voice.speech_manager import speech_manager
            audio_info = speech_manager.synthesize_and_stage(resp_text, play_system=req.audio_output == "system")
            if not audio_info.get("audio_url"):
                result["audio_error"] = audio_info.get("error") or "Speech synthesis produced no playable audio"
            result["audio_id"] = audio_info.get("audio_id")
            result["audio_url"] = audio_info.get("audio_url")
            result["audio_provider"] = audio_info.get("provider")
            result["audio_provider_label"] = audio_info.get("provider_label")
            result["is_cloned"] = audio_info.get("is_cloned", False)
        except Exception as ae:
            logger.warning(f"Voice generation error in chat: {ae}")

    return result


@chat_router.post("/stream")
def chat_stream_endpoint(req: ChatRequest):
    """
    Stream chat tokens in real-time using Server-Sent Events (SSE).
    Text-first delivery: text is progressively streamed with immediate rendering.
    Audio is only staged post-stream if req.speak is True.
    """
    if req.speak:
        try:
            from apps.voice.service import voice_service
            voice_service.stop_playback()
        except Exception:
            pass
        try:
            from apps.voice.speech_manager import speech_manager
            speech_manager.stop()
        except Exception:
            pass

    from ai.brain import get_brain
    brain = get_brain()

    def event_stream():
        full_text = ""
        successful = False
        events = None
        try:
            yield f"data: {json.dumps({'type': 'accepted', 'message': 'Message received. I am working on it.'})}\n\n"
            events = brain.stream_chat(
                user_message=req.message,
                session_id=req.session_id,
                provider_name=req.provider,
                model_name=req.model,
                use_tools=req.use_tools,
                allow_fallback=req.allow_fallback,
                max_provider_retries=req.max_provider_retries,
            )
            for event in events:
                if event.get("type") == "token":
                    full_text += event.get("content", "")
                if event.get('type') == 'done':
                    successful = not event.get('error') and event.get('status') not in {'failed', 'cancelled'}
                payload = json.dumps(event)
                yield f"data: {payload}\n\n"

            # Optional post-stream speech synthesis if explicitly enabled
            if req.speak and successful and full_text.strip():
                try:
                    from apps.voice.speech_manager import speech_manager
                    audio_info = speech_manager.synthesize_and_stage(full_text.strip(), play_system=req.audio_output == "system")
                    if not audio_info.get("audio_url"):
                        yield f"data: {json.dumps({'type': 'audio_error', 'message': audio_info.get('error') or 'Speech synthesis produced no playable audio'})}\n\n"
                        return
                    audio_event = {
                        "type": "audio",
                        "audio_id": audio_info.get("audio_id"),
                        "audio_url": audio_info.get("audio_url"),
                        "playback_target": req.audio_output,
                        "provider": audio_info.get("provider"),
                        "provider_label": audio_info.get("provider_label"),
                        "is_cloned": audio_info.get("is_cloned", False),
                    }
                    yield f"data: {json.dumps(audio_event)}\n\n"
                except Exception as ae:
                    logger.warning(f"Post-stream audio error: {ae}")
                    yield f"data: {json.dumps({'type': 'audio_error', 'message': 'Speech synthesis failed'})}\n\n"

        except Exception as e:
            logger.error(f"Event stream error: {e}")
            err_payload = json.dumps({"type": "error", "message": "The reply was interrupted. Check task results before retrying."})
            yield f"data: {err_payload}\n\n"
        finally:
            if events is not None and hasattr(events, 'close'):
                events.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@chat_router.get("/providers")
def get_providers_endpoint():
    """Retrieve all configured AI providers, availability status, and installed models."""
    from ai.brain import get_brain
    brain = get_brain()
    return brain.get_providers_status()


@chat_router.post("/model")
def switch_model_endpoint(req: ModelSwitchRequest):
    """Dynamically switch the active AI provider and/or target model."""
    from ai.brain import get_brain
    brain = get_brain()
    success = brain.set_active_provider(req.provider, req.model)
    return {
        "success": success,
        "active_provider": brain._active.name if brain._active else req.provider,
        "active_model": getattr(brain._active, "model", req.model or ""),
    }


@chat_router.get("/status")
def ai_status():
    """Check status of all AI providers."""
    from ai.brain import get_brain
    brain = get_brain()
    return brain.status()


@chat_router.get("/history")
def get_history_endpoint(session_id: Optional[str] = None):
    """Retrieve dialogue history turns from persistent SQLite store."""
    from memory.long_term.database import db
    from ai.brain import get_brain
    brain = get_brain()
    sid = session_id or "default"
    db_turns = db.get_session_messages(sid, limit=50)
    history = [
        {
            "role": t["role"],
            "text": t["content"],
            "content": t["content"],
            "timestamp": t["timestamp"],
            "message_id": t["message_id"],
            "provider": t["provider"],
            "model": t["model"],
            "tools_used": t["tools_used"],
        }
        for t in db_turns
    ]
    return {"status": "ok", "session_id": sid, "history": history, "count": len(history)}


@chat_router.delete("/history")
def clear_history(session_id: Optional[str] = None):
    """Clear conversation history for a specific session."""
    from memory.long_term.database import db
    from ai.brain import get_brain
    brain = get_brain()
    sid = session_id or "default"
    if sid in brain._sessions:
        brain._sessions[sid].clear()
    count = db.clear_session_messages(sid)
    return {"status": "cleared", "session_id": sid, "deleted_count": count}


class PromptTestRequest(BaseModel):
    system_prompt: Optional[str] = None
    user_message: str = Field(..., min_length=1)
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024


@chat_router.post("/prompt_test")
def test_prompt(req: PromptTestRequest):
    """Direct playground test endpoint for AI Studio."""
    import time
    from ai.brain import get_brain
    brain = get_brain()
    t0 = time.perf_counter()
    if req.provider:
        brain.set_active_provider(req.provider, req.model)
    res = brain.chat(
        user_message=req.user_message,
        use_tools=False,
    )
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "status": "ok",
        "response": res.get("response", ""),
        "provider": res.get("provider", "unknown"),
        "model": res.get("model", ""),
        "latency_ms": latency_ms,
        "token_usage": res.get("token_usage", {}),
    }
