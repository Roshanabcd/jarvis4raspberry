"""Pure-Python financial technical indicators (zero compiled C dependencies)."""

from __future__ import annotations

import math
from typing import List, Tuple


def sma(values: List[float], period: int) -> List[float]:
    if not values or period <= 0:
        return []
    out: List[float] = []
    running = 0.0
    for i, v in enumerate(values):
        running += v
        if i >= period:
            running -= values[i - period]
            out.append(running / period)
        else:
            out.append(running / (i + 1))
    return out


def ema(values: List[float], period: int) -> List[float]:
    if not values or period <= 0:
        return []
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1.0 - k))
    return out


def rsi(values: List[float], period: int = 14) -> List[float]:
    if len(values) < 2:
        return [50.0] * len(values)
    gains: List[float] = [0.0]
    losses: List[float] = [0.0]
    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    avg_gain = sum(gains[1 : period + 1]) / max(1, min(period, len(values) - 1))
    avg_loss = sum(losses[1 : period + 1]) / max(1, min(period, len(values) - 1))

    out: List[float] = []
    for i in range(len(values)):
        if i <= period:
            g = sum(gains[1 : i + 1]) / max(1, i)
            l = sum(losses[1 : i + 1]) / max(1, i)
        else:
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            g, l = avg_gain, avg_loss
        if l == 0:
            out.append(100.0 if g > 0 else 50.0)
        else:
            rs = g / l
            out.append(100.0 - (100.0 / (1.0 + rs)))
    return out


def macd(values: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[List[float], List[float]]:
    fast_ema = ema(values, fast)
    slow_ema = ema(values, slow)
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal_period)
    return macd_line, signal_line


def bollinger_bands(values: List[float], period: int = 20, num_std: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
    mid = sma(values, period)
    upper: List[float] = []
    lower: List[float] = []
    for i in range(len(values)):
        window = values[max(0, i - period + 1) : i + 1]
        mean = mid[i]
        var = sum((x - mean) ** 2 for x in window) / max(1, len(window))
        std = math.sqrt(var)
        upper.append(mean + num_std * std)
        lower.append(mean - num_std * std)
    return upper, mid, lower


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    if not closes:
        return []
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    return sma(trs, period)
