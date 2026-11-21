"""Pydantic v1/v2 compatible schemas for JARVIS Module 34 — Personal Finance Manager."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class AccountCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    account_type: Literal["checking", "savings", "credit", "cash", "investment"] = Field(default="checking")
    currency: str = Field(default="USD", min_length=3, max_length=6)
    opening_balance: float = Field(default=0.0)


class TransactionCreateRequest(BaseModel):
    account_id: str
    tx_type: Literal["income", "expense"]
    amount: float = Field(..., gt=0.0)
    category: str = Field(..., min_length=2, max_length=60)
    merchant: str = Field(default="", max_length=120)
    tx_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    note: str = Field(default="", max_length=300)


class BudgetUpsertRequest(BaseModel):
    month: str = Field(..., min_length=7, max_length=7, description="YYYY-MM")
    category: str = Field(..., min_length=2, max_length=60)
    limit_amount: float = Field(..., gt=0.0)


class GoalCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    target_amount: float = Field(..., gt=0.0)
    current_amount: float = Field(default=0.0, ge=0.0)
    target_date: str = Field(default="", max_length=20)


class GoalContributeRequest(BaseModel):
    amount: float = Field(..., gt=0.0)
