"""Pydantic schemas for JARVIS Module 22 (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()


class ModelRegisterRequest(BaseModel):
    model_id: str = Field(..., min_length=2, max_length=80)
    provider: str = Field(..., min_length=2, max_length=50)
    display_name: str = Field(..., min_length=2, max_length=120)
    capabilities: List[str] = Field(default_factory=lambda: ["general"])
    cost_per_1k_input_usd: float = Field(default=0.0, ge=0.0)
    cost_per_1k_output_usd: float = Field(default=0.0, ge=0.0)
    avg_latency_ms: int = Field(default=350, ge=10, le=60000)
    quality_score: float = Field(default=0.8, ge=0.0, le=1.0)
    max_context_tokens: int = Field(default=32768, ge=512)
    privacy_tier: str = Field(default="cloud", description="local | cloud")
    enabled: bool = Field(default=True)


class ModelToggleRequest(BaseModel):
    enabled: Optional[bool] = None
    simulate_outage: Optional[bool] = None
    reset_circuit: bool = False


class RouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=16000)
    task_type: str = Field(default="auto", description="auto | general | coding | reasoning | summarization | vision")
    strategy: str = Field(default="balanced", description="balanced | cost_optimized | latency_optimized | quality_first | local_only")
    max_cost_usd: Optional[float] = Field(default=None, ge=0.0)
    require_local: bool = Field(default=False)
    use_cache: bool = Field(default=True)
    preferred_model_id: Optional[str] = None


class BenchmarkRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    model_ids: List[str] = Field(..., min_items=1, max_items=6)
    task_type: str = Field(default="auto")


class BudgetUpdateRequest(BaseModel):
    daily_budget_usd: Optional[float] = Field(default=None, ge=0.0)
    downgrade_to_local_on_cap: Optional[bool] = None
    enable_cache: Optional[bool] = None
