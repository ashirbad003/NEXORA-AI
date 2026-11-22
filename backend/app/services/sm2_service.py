import math
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class SM2CalculationResult:
    repetition: int
    interval_days: int
    ease_factor: float
    stability: float
    next_review_at: datetime

class SM2Engine:
    """
    SuperMemo-2 (SM-2) Spaced Repetition Engine with Stability Tracking.
    Canonical mathematical formulation:
      EF' = max(1.30, round(EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)), 2))
      If q < 3 (failure):
        repetition' = 0
        interval' = 1
        stability' = max(1.0, round(stability / 3.0, 2))
      If q >= 3 (success):
        repetition' = repetition + 1
        interval' = 1 if repetition' == 1 else 6 if repetition' == 2 else max(1, math.floor(interval * EF' + 0.5))
        stability' = round(stability * (1.0 + (EF' - 1.2) * 0.5), 2)
    """

    MIN_EASE_FACTOR: float = 1.30
    DEFAULT_EASE_FACTOR: float = 2.50
    DEFAULT_STABILITY: float = 1.00

    @classmethod
    def calculate(
        cls,
        current_repetition: int,
        current_interval: int,
        current_ease_factor: float,
        current_stability: float,
        grade: int,
        review_time: datetime | None = None
    ) -> SM2CalculationResult:
        if not (0 <= grade <= 5):
            raise ValueError(f"SM-2 grade must be an integer between 0 and 5 inclusive, got {grade}")

        now = review_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # 1. Update Ease Factor (applicable across all grades 0..5)
        ef_delta = 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)
        new_ef = round(max(cls.MIN_EASE_FACTOR, current_ease_factor + ef_delta), 2)

        # 2. Determine Repetition, Interval, and Stability
        if grade < 3:
            # Lapse / Failure
            new_rep = 0
            new_interval = 1
            new_stability = max(1.0, round(current_stability / 3.0, 2))
        else:
            # Successful Recall
            new_rep = current_repetition + 1
            if new_rep == 1:
                new_interval = 1
            elif new_rep == 2:
                new_interval = 6
            else:
                new_interval = max(1, math.floor(current_interval * new_ef + 0.5))
            
            # Stability grows with ease factor
            new_stability = round(current_stability * (1.0 + (new_ef - 1.2) * 0.5), 2)

        next_review_at = now + timedelta(days=new_interval)

        return SM2CalculationResult(
            repetition=new_rep,
            interval_days=new_interval,
            ease_factor=new_ef,
            stability=new_stability,
            next_review_at=next_review_at
        )

    @staticmethod
    def calculate_retention_probability(stability: float, days_since_review: float) -> float:
        """
        Ebbinghaus retention probability: R = exp(-t / S)
        Where t is days elapsed, S is memory stability in days.
        """
        if stability <= 0:
            return 0.0
        return round(math.exp(-max(0.0, days_since_review) / stability), 4)
