"""Odds-weighted prediction scoring (betting-style).

Points for a correct pick scale inversely with the pre-match win probability of
the team you picked — calling an underdog is worth far more than the favorite.
Wrong picks score 0. Probability is clamped so payouts stay bounded.
"""

BASE_POINTS = 100
MIN_P = 0.1   # cap upset payout at BASE/MIN_P = 1000
MAX_P = 0.9   # floor favorite payout at BASE/MAX_P ≈ 111


def prediction_points(prob_of_pick: float, correct: bool) -> int:
    if not correct:
        return 0
    p = min(max(prob_of_pick, MIN_P), MAX_P)
    return round(BASE_POINTS / p)
