import pytest

from app.domain.scoring import InvalidScore, ScoringRules, resolve_winner

NO_WIN_BY_TWO = ScoringRules(target_points=11, win_by_two=False)
WIN_BY_TWO = ScoringRules(target_points=11, win_by_two=True)
WIN_BY_TWO_CAP = ScoringRules(target_points=11, win_by_two=True, maximum_points=15)


def test_no_win_by_two_valid():
    assert resolve_winner(NO_WIN_BY_TWO, 11, 0) == "A"
    assert resolve_winner(NO_WIN_BY_TWO, 11, 10) == "A"
    assert resolve_winner(NO_WIN_BY_TWO, 7, 11) == "B"


@pytest.mark.parametrize("a,b", [(10, 10), (12, 10), (11, 11), (9, 8)])
def test_no_win_by_two_invalid(a, b):
    with pytest.raises(InvalidScore):
        resolve_winner(NO_WIN_BY_TWO, a, b)


def test_negative_and_draw_invalid():
    with pytest.raises(InvalidScore):
        resolve_winner(NO_WIN_BY_TWO, -1, 11)
    with pytest.raises(InvalidScore):
        resolve_winner(NO_WIN_BY_TWO, 5, 5)


def test_win_by_two():
    assert resolve_winner(WIN_BY_TWO, 11, 8) == "A"
    assert resolve_winner(WIN_BY_TWO, 12, 10) == "A"
    assert resolve_winner(WIN_BY_TWO, 13, 15) == "B"
    with pytest.raises(InvalidScore):
        resolve_winner(WIN_BY_TWO, 11, 10)  # lead of 1, not at a cap


def test_win_by_two_with_cap():
    assert resolve_winner(WIN_BY_TWO_CAP, 15, 14) == "A"  # one-point win allowed at cap
    with pytest.raises(InvalidScore):
        resolve_winner(WIN_BY_TWO_CAP, 16, 14)  # exceeds cap
