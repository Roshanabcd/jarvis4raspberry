"""Pydantic v1/v2 compatible schemas for JARVIS Module 28 — AI Data Analyst."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class DatasetCSVRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)
    csv_text: str = Field(..., min_length=5, max_length=500000)


class DatasetRowsRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)
    rows: List[Dict[str, Any]] = Field(..., min_items=1)


class AggregateRequest(BaseModel):
    group_by: str = Field(..., min_length=1, max_length=80)
    metric: str = Field(..., min_length=1, max_length=80)
    agg: Literal["sum", "avg", "min", "max", "count"] = Field(default="sum")


class AnomalyRequest(BaseModel):
    column: str = Field(..., min_length=1, max_length=80)
    z_threshold: float = Field(default=2.0, ge=0.5, le=10.0)


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
