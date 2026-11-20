"""Typed Pydantic v1/v2 compatible schemas for Deep Learning Recommendation Engine."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Deep Learning Recommendation Engine"
    version: str = "1.0.0"
    embedding_dim: int
    total_items: int
    total_interactions: int


class CatalogItemRequest(BaseModel):
    item_id: str = Field(..., min_length=1, max_length=120)
    title: str = Field(..., min_length=2, max_length=200)
    category: str = Field(default="general", max_length=80)
    description: str = Field(..., min_length=5, max_length=3000)
    tags: List[str] = Field(default_factory=list)


class CatalogItemRecord(BaseModel):
    item_id: str
    created_at: str
    title: str
    category: str
    description: str
    tags: List[str]


class CatalogListResponse(BaseModel):
    total: int
    items: List[CatalogItemRecord]


class InteractionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=120)
    item_id: str = Field(..., min_length=1, max_length=120)
    event_type: str = Field(default="like", max_length=40)  # view | like | bookmark | complete | dismiss
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)


class InteractionRecord(BaseModel):
    id: int
    created_at: str
    user_id: str
    item_id: str
    event_type: str
    weight: float


class RecommendationRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=120)
    top_k: int = Field(default=5, ge=1, le=50)
    category_filter: Optional[str] = None
    exclude_interacted: bool = True


class RecommendedItem(BaseModel):
    item_id: str
    title: str
    category: str
    tags: List[str]
    final_score: float
    content_cosine: float
    collaborative_score: float
    latent_mf_score: float
    reason: str


class RecommendationResponse(BaseModel):
    user_id: str
    strategy: str
    recommendations: List[RecommendedItem]


class SimilarItemsResponse(BaseModel):
    source_item_id: str
    similar: List[RecommendedItem]
