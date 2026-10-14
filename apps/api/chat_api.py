"""
JARVIS Chat API — Uses the real AI brain with tool calling.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
import logging

logger = logging.getLogger("JARVIS.API.Chat")
chat_router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    session_id: Optional[str] = None
    use_tools: bool = True


@chat_router.post("")
def chat_endpoint(req: ChatRequest):
    """Process a chat message through the JARVIS AI brain."""
    from ai.brain import get_brain
    brain = get_brain()
    result = brain.chat(
        user_message=req.message,
        use_tools=req.use_tools,
        session_id=req.session_id,
    )
    return result


@chat_router.get("/status")
def ai_status():
    """Check status of all AI providers."""
    from ai.brain import get_brain
    brain = get_brain()
    return brain.status()


@chat_router.delete("/history")
def clear_history():
    """Clear conversation history."""
    from ai.brain import get_brain
    brain = get_brain()
    brain._history.clear()
    return {"status": "cleared"}
