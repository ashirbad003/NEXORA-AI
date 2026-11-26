import { LocalSM2Engine } from '../services/localSm2';

describe('LocalSM2Engine Differential & Precision Tests', () => {
  it('grade 0 (blackout): ef drops by 0.8, rep=0, interval=1, stability degrades', () => {
    // ef_delta = 0.1 - (5 - 0) * (0.08 + 5 * 0.02) = 0.1 - 5 * 0.18 = 0.1 - 0.9 = -0.8
    // new_ef = max(1.30, 2.50 - 0.80) = 1.70
    // new_rep = 0, new_interval = 1, stability = max(1.0, round(2.0/3, 2)) = 1.0
    const res = LocalSM2Engine.calculate(2, 6, 2.50, 2.00, 0);
    expect(res.repetition).toBe(0);
    expect(res.interval_days).toBe(1);
    expect(res.ease_factor).toBe(1.70);
    expect(res.stability).toBe(1.00);
  });

  it('grade 3 (pass threshold): ef drops by 0.14, rep advances to 3, interval uses formula', () => {
    // ef_delta = 0.1 - (5 - 3) * (0.08 + 2 * 0.02) = 0.1 - 2 * 0.12 = 0.1 - 0.24 = -0.14
    // new_ef = max(1.30, 2.50 - 0.14) = 2.36
    // rep 2 -> 3: interval = max(1, floor(6 * 2.36 + 0.5)) = floor(14.16 + 0.5) = floor(14.66) = 14
    // stability = round(1.65 * (1.0 + (2.36 - 1.2)*0.5), 2) = round(1.65 * (1.0 + 0.58), 2) = round(1.65 * 1.58, 2) = 2.61
    const res = LocalSM2Engine.calculate(2, 6, 2.50, 1.65, 3);
    expect(res.repetition).toBe(3);
    expect(res.interval_days).toBe(14);
    expect(res.ease_factor).toBe(2.36);
    expect(res.stability).toBe(2.61);
  });

  it('grade 5 (bonus/easy): ef increases by 0.10, rep advances, interval expands', () => {
    // ef_delta = 0.1 - 0 = +0.10
    // new_ef = 2.36 + 0.10 = 2.46
    // rep 3 -> 4: interval = max(1, floor(14 * 2.46 + 0.5)) = floor(34.44 + 0.5) = floor(34.94) = 34
    const res = LocalSM2Engine.calculate(3, 14, 2.36, 2.61, 5);
    expect(res.repetition).toBe(4);
    expect(res.interval_days).toBe(34);
    expect(res.ease_factor).toBe(2.46);
    expect(res.stability).toBeGreaterThan(2.61);
  });

  it('preserves ISO next_review_at date with exact day offset', () => {
    const fixedNow = new Date('2026-11-26T12:00:00Z');
    const res = LocalSM2Engine.calculate(0, 0, 2.5, 1.0, 4, fixedNow);
    expect(res.next_review_at).toBe('2026-11-27T12:00:00.000Z');
  });
});
