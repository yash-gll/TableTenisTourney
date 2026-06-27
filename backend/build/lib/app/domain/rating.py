"""Pure Elo rating math.

    team_rating  = average(player_1, player_2)
    expected_a   = 1 / (1 + 10 ** ((team_b - team_a) / 400))
    delta        = K * (actual - expected)     (winner actual=1, loser=0)

Both players on a team receive the same delta. Ratings are integers; each delta
is rounded so a chronological replay is deterministic.
"""

from dataclasses import dataclass

from app.db.models.enums import MatchStage


@dataclass(frozen=True)
class RatingConfigValues:
    starting_rating: int = 1000
    rating_floor: int = 100
    group_k: int = 20
    qf1_k: int = 24
    qf2_k: int = 24
    qf3_k: int = 28
    final_k: int = 32
    champion_bonus: int = 50
    runner_up_bonus: int = 15
    third_place_bonus: int = 5


def team_rating(r1: int, r2: int) -> float:
    return (r1 + r2) / 2


def expected_score(team_a: float, team_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((team_b - team_a) / 400.0))


def compute_delta(k: int, actual: float, expected: float) -> int:
    return round(k * (actual - expected))


def stage_k(stage: MatchStage, cfg: RatingConfigValues) -> int:
    return {
        MatchStage.GROUP: cfg.group_k,
        MatchStage.QF1: cfg.qf1_k,
        MatchStage.QF2: cfg.qf2_k,
        MatchStage.QF3: cfg.qf3_k,
        MatchStage.FINAL: cfg.final_k,
        MatchStage.TIEBREAKER: cfg.group_k,
    }[stage]


def placement_bonus(place: int, cfg: RatingConfigValues) -> int:
    return {1: cfg.champion_bonus, 2: cfg.runner_up_bonus, 3: cfg.third_place_bonus}.get(place, 0)


def apply_floor(rating: int, cfg: RatingConfigValues) -> int:
    return max(cfg.rating_floor, rating)


@dataclass(frozen=True)
class MatchDeltas:
    """Per-team deltas for one match (each teammate gets the team's delta)."""

    delta_a: int
    delta_b: int
    expected_a: float
    expected_b: float


def match_deltas(
    *,
    team_a_rating: float,
    team_b_rating: float,
    winner_is_a: bool,
    k: int,
) -> MatchDeltas:
    exp_a = expected_score(team_a_rating, team_b_rating)
    exp_b = 1.0 - exp_a
    actual_a = 1.0 if winner_is_a else 0.0
    actual_b = 1.0 - actual_a
    return MatchDeltas(
        delta_a=compute_delta(k, actual_a, exp_a),
        delta_b=compute_delta(k, actual_b, exp_b),
        expected_a=exp_a,
        expected_b=exp_b,
    )
