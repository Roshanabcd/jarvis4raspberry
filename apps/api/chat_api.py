"""
JARVIS Chat API — Real AI brain with streaming SSE, tool calling, and multi-provider switching.
"""
import json
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter
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


class ModelSwitchRequest(BaseModel):
    provider: str = Field(..., min_length=1)
    model: Optional[str] = None


@chat_router.post("")
def chat_endpoint(req: ChatRequest) -> Dict[str, Any]:
    """Process a chat message through the JARVIS AI brain synchronously."""
    from ai.brain import get_brain
    from apps.voice.speech_manager import speech_manager
    brain = get_brain()
    if req.provider:
        brain.set_active_provider(req.provider, req.model)

    result = brain.chat(
        user_message=req.message,
        use_tools=req.use_tools,
        session_id=req.session_id,
    )
    # Generate speech for every final response and speak through physical speaker
    resp_text = result.get("response", "")
    if resp_text:
        try:
            audio_info = speech_manager.synthesize_and_stage(resp_text, play_system=True)
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
    Generates audio on completion and streams audio_url event.
    """
    from ai.brain import get_brain
    from apps.voice.speech_manager import speech_manager
    brain = get_brain()

    def event_stream():
        full_text = ""
        try:
            for event in brain.stream_chat(
                user_message=req.message,
                session_id=req.session_id,
                provider_name=req.provider,
                model_name=req.model,
            ):
                if event.get("type") == "token":
                    full_text += event.get("content", "")
                payload = json.dumps(event)
                yield f"data: {payload}\n\n"

            # Stream complete: synthesize speech for the full final response and speak through speaker
            if full_text.strip():
                try:
                    audio_info = speech_manager.synthesize_and_stage(full_text.strip(), play_system=True)
                    audio_event = {
                        "type": "audio",
                        "audio_id": audio_info.get("audio_id"),
                        "audio_url": audio_info.get("audio_url"),
                        "provider": audio_info.get("provider"),
                        "provider_label": audio_info.get("provider_label"),
                        "is_cloned": audio_info.get("is_cloned", False),
                    }
                    yield f"data: {json.dumps(audio_event)}\n\n"
                except Exception as ae:
                    logger.warning(f"Post-stream audio error: {ae}")

        except Exception as e:
            logger.error(f"Event stream error: {e}")
            err_payload = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {err_payload}\n\n"

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
def get_history_endpoint():
    """Retrieve dialogue history turns."""
    from ai.brain import get_brain
    from apps.voice.service import voice_service
    brain = get_brain()
    history = []
    if hasattr(brain, "_history") and brain._history:
        for item in brain._history:
            history.append({
                "role": item.get("role", "user"),
                "text": item.get("content", item.get("text", "")),
                "timestamp": item.get("timestamp"),
            })
    elif hasattr(voice_service, "conversation") and voice_service.conversation:
        conv = voice_service.conversation
        turns = conv.get_turns(50) if hasattr(conv, "get_turns") else getattr(conv, "turns", [])
        for t in turns:
            history.append({
                "role": t.get("role", "user"),
                "text": t.get("text", ""),
                "timestamp": t.get("timestamp"),
            })
    return {"status": "ok", "history": history, "count": len(history)}


@chat_router.delete("/history")
def clear_history():
    """Clear conversation history."""
    from ai.brain import get_brain
    brain = get_brain()
    brain._history.clear()
    return {"status": "cleared"}


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
