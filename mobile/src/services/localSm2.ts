export interface SM2Result {
  repetition: int;
  interval_days: number;
  ease_factor: number;
  stability: number;
  next_review_at: string;
}

type int = number;

/**
 * Local SM-2 Spaced Repetition Engine
 * Strictly equivalent to backend/app/services/sm2_service.py:
 *
 * EF' = max(1.30, round(EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)), 2))
 * If q < 3 (failure):
 *   repetition' = 0
 *   interval' = 1
 *   stability' = max(1.0, round(stability / 3.0, 2))
 * If q >= 3 (success):
 *   repetition' = repetition + 1
 *   interval' = 1 if repetition' == 1 else 6 if repetition' == 2 else max(1, math.floor(interval * EF' + 0.5))
 *   stability' = round(stability * (1.0 + (EF' - 1.2) * 0.5), 2)
 */
export const LocalSM2Engine = {
  MIN_EASE_FACTOR: 1.30,
  DEFAULT_EASE_FACTOR: 2.50,
  DEFAULT_STABILITY: 1.00,

  calculate(
    currentRepetition: number,
    currentInterval: number,
    currentEaseFactor: number,
    currentStability: number,
    grade: number,
    reviewDate: Date = new Date()
  ): SM2Result {
    if (grade < 0 || grade > 5 || !Number.isInteger(grade)) {
      throw new Error(`SM-2 grade must be an integer between 0 and 5, received ${grade}`);
    }

    // 1. Ease Factor update
    const efDelta = 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02);
    const newEf = Math.round(Math.max(this.MIN_EASE_FACTOR, currentEaseFactor + efDelta) * 100) / 100;

    let newRep: number;
    let newInterval: number;
    let newStability: number;

    if (grade < 3) {
      newRep = 0;
      newInterval = 1;
      newStability = Math.max(1.0, Math.round((currentStability / 3.0) * 100) / 100);
    } else {
      newRep = currentRepetition + 1;
      if (newRep === 1) {
        newInterval = 1;
      } else if (newRep === 2) {
        newInterval = 6;
      } else {
        newInterval = Math.max(1, Math.floor(currentInterval * newEf + 0.5));
      }
      newStability = Math.round(currentStability * (1.0 + (newEf - 1.2) * 0.5) * 100) / 100;
    }

    const nextReview = new Date(reviewDate.getTime() + newInterval * 24 * 60 * 60 * 1000);

    return {
      repetition: newRep,
      interval_days: newInterval,
      ease_factor: newEf,
      stability: newStability,
      next_review_at: nextReview.toISOString(),
    };
  },
};
