"""Environment-driven configuration for JARVIS Fraud Detection System."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_FRAUD_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_fraud_detection" / "fraud_detection.db").resolve()


@dataclass(frozen=True)
class FraudDetectionConfig:
    """Immutable runtime settings for anomaly and fraud detection."""

    db_path: Path = field(default_factory=_default_db_path)
    review_threshold: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_FRAUD_REVIEW_THRESHOLD", "45.0"))
    )
    block_threshold: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_FRAUD_BLOCK_THRESHOLD", "75.0"))
    )
    velocity_window_minutes: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_FRAUD_VELOCITY_WINDOW_MIN", "15"))
    )
    high_amount_baseline: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_FRAUD_HIGH_AMOUNT", "2500.0"))
    )
