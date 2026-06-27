from app.db.models.enums import MatchStage
from app.domain.rating import (
    RatingConfigValues,
    apply_floor,
    expected_score,
    match_deltas,
    placement_bonus,
    stage_k,
)

CFG = RatingConfigValues()


def test_equal_teams_expected_half():
    assert expected_score(1000, 1000) == 0.5


def test_upset_beats_favorite_gain():
    upset = match_deltas(team_a_rating=1000, team_b_rating=1400, winner_is_a=True, k=20)
    favorite = match_deltas(team_a_rating=1000, team_b_rating=1400, winner_is_a=False, k=20)
    # Underdog (A) winning gains far more than favorite (B) winning.
    assert upset.delta_a > favorite.delta_b
    assert upset.delta_a > 15 and favorite.delta_b < 5


def test_stage_k_values():
    assert stage_k(MatchStage.GROUP, CFG) == 20
    assert stage_k(MatchStage.QF1, CFG) == 24
    assert stage_k(MatchStage.QF3, CFG) == 28
    assert stage_k(MatchStage.FINAL, CFG) == 32


def test_placement_bonus():
    assert placement_bonus(1, CFG) == 50
    assert placement_bonus(2, CFG) == 15
    assert placement_bonus(3, CFG) == 5
    assert placement_bonus(4, CFG) == 0


def test_winner_gains_loser_loses_symmetric():
    d = match_deltas(team_a_rating=1000, team_b_rating=1000, winner_is_a=True, k=20)
    assert d.delta_a == 10 and d.delta_b == -10  # K/2 at even odds


def test_floor():
    assert apply_floor(50, CFG) == 100
    assert apply_floor(900, CFG) == 900
