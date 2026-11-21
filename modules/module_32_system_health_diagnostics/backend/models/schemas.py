"""Pydantic v1/v2 compatible schemas for JARVIS Module 32 — System Health & Diagnostics."""

from __future__ import annotations

from typing import Any, Dict, Literal
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class AlertRuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    metric_key: Literal["load_1m", "memory_used_pct", "disk_used_pct", "cpu_temp_c"]
    operator: Literal[">", ">=", "<", "<="] = Field(default=">")
    threshold: float
    severity: Literal["warning", "critical"] = Field(default="warning")


class ServiceCheckCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    host: str = Field(default="127.0.0.1", min_length=1, max_length=64)
    port: int = Field(..., ge=1, le=65535)
