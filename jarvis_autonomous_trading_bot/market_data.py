"""Deterministic synthetic OHLCV generator for offline simulation & backtesting."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta, timezone
from typing import List

from .models import Candle


def generate_synthetic_candles(symbol: str, bars: int = 150) -> List[Candle]:
    """Produce deterministic, realistic trending + oscillating OHLCV bars for offline testing."""
    seed = int(hashlib.sha256(symbol.upper().encode("utf-8")).hexdigest()[:8], 16)
    base_price = 100.0 + (seed % 400)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=bars)

    candles: List[Candle] = []
    price = base_price
    for i in range(bars):
        # Smooth multi-frequency wave + slight drift so crossover & RSI strategies trigger realistically
        cycle = math.sin((i + (seed % 17)) / 9.5) * 0.018 + math.cos(i / 23.0) * 0.011
        drift = 0.0006
        open_p = price
        close_p = max(1.0, open_p * (1.0 + cycle + drift))
        high_p = max(open_p, close_p) * (1.0 + 0.004 + (i % 5) * 0.001)
        low_p = min(open_p, close_p) * (1.0 - 0.004 - (i % 4) * 0.001)
        vol = 1000.0 + ((seed + i * 97) % 5000)

        candles.append(
            Candle(
                timestamp=(start + timedelta(hours=i)).isoformat(),
                open=round(open_p, 4),
                high=round(high_p, 4),
                low=round(max(0.5, low_p), 4),
                close=round(close_p, 4),
                volume=float(vol),
            )
        )
        price = close_p
    return candles
