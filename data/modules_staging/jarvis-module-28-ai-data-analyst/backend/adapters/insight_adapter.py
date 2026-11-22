"""Narrative insight synthesis adapter contract for Module 28."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class DataInsightAdapter(ABC):
    adapter_name: str = "abstract_data_insight"
    is_simulated: bool = True

    @abstractmethod
    def synthesize_narrative(self, dataset_name: str, profile: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> str:
        """Return a concise executive narrative from computed statistics and anomalies."""


class LocalDataInsightAdapter(DataInsightAdapter):
    """Deterministic local narrative generator (no external LLM credentials required)."""

    adapter_name = "local_statistical_narrative_adapter"
    is_simulated = True

    def synthesize_narrative(self, dataset_name: str, profile: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> str:
        num_cols = [c["name"] for c in profile["columns"] if c["dtype"] == "numeric"]
        cat_cols = [c["name"] for c in profile["columns"] if c["dtype"] == "categorical"]
        return (
            f"[LOCAL ANALYST SUMMARY] Dataset '{dataset_name}' contains {profile['row_count']} rows "
            f"across {len(profile['columns'])} columns ({len(num_cols)} numeric: {', '.join(num_cols) or 'none'}; "
            f"{len(cat_cols)} categorical: {', '.join(cat_cols) or 'none'}). "
            f"Detected {len(anomalies)} Z-score anomaly candidate(s)."
        )
