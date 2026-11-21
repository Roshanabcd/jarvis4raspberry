"""Pydantic v1/v2 compatible schemas for JARVIS Module 35 — Visual Workflow Builder."""

from __future__ import annotations

from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class WorkflowNode(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=64)
    node_type: Literal["trigger", "transform", "condition", "math", "notify"]
    label: str = Field(..., min_length=1, max_length=120)
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    source: str = Field(..., min_length=1, max_length=64)
    target: str = Field(..., min_length=1, max_length=64)


class WorkflowCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=300)
    nodes: List[WorkflowNode] = Field(..., min_items=1)
    edges: List[WorkflowEdge] = Field(default_factory=list)


class WorkflowExecuteRequest(BaseModel):
    input_data: Dict[str, Any] = Field(default_factory=dict)
