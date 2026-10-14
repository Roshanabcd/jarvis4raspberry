"""AI Model Router package."""

from ai.router.model_router import ModelRouter

AIRouter = ModelRouter
ai_router = ModelRouter()

__all__ = ["ModelRouter", "AIRouter", "ai_router"]
