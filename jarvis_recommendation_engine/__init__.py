"""JARVIS OS — Deep Learning Recommendation Engine (Additive Feature Module #9).

Personalized content and task recommendations using collaborative filtering,
SGD latent-factor embeddings, and 128-D dense embedding cosine similarities.
"""

from .config import RecommendationConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["RecommendationConfig", "create_router", "__version__"]
