"""SuperMemo SM-2 spaced-repetition scheduler."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Tuple


def compute_sm2(
    quality: int,
    repetitions: int,
    interval_days: int,
    ease_factor: float,
    today: date | None = None,
) -> Tuple[int, int, float, str]:
    """Return (new_repetitions, new_interval_days, new_ease_factor, next_review_iso_date).

    quality: integer 0..5 (0-2 = forgotten/reset, 3 = hard, 4 = good, 5 = easy).
    """
    q = max(0, min(5, int(quality)))
    base_date = today or date.today()

    if q < 3:
        new_reps = 0
        new_interval = 1
    else:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(interval_days * ease_factor))
        new_reps = repetitions + 1

    new_ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = round(max(1.3, new_ef), 2)
    next_date = (base_date + timedelta(days=new_interval)).isoformat()
    return new_reps, new_interval, new_ef, next_date
