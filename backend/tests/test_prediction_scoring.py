from app.domain.prediction_scoring import prediction_points


def test_wrong_pick_scores_zero():
    assert prediction_points(0.5, False) == 0
    assert prediction_points(0.2, False) == 0


def test_even_odds():
    assert prediction_points(0.5, True) == 200


def test_underdog_beats_favorite():
    favorite = prediction_points(0.8, True)
    underdog = prediction_points(0.2, True)
    assert underdog > favorite
    assert favorite == 125 and underdog == 500


def test_payout_is_clamped():
    # Extreme favorites/longshots are bounded.
    assert prediction_points(0.99, True) == round(100 / 0.9)  # ≈ 111
    assert prediction_points(0.01, True) == 1000  # 100 / 0.1
