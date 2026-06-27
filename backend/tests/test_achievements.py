from app.domain.achievements import AchievementInput, earned_badges
from tests.conftest import make_approved_player


def _keys(**kw):
    base = dict(
        titles=0, finals_reached=0, podiums=0, matches_played=0, wins=0, longest_win_streak=0
    )
    base.update(kw)
    return {b.key for b in earned_badges(AchievementInput(**base))}


def test_champion_and_dynasty():
    assert "champion" in _keys(titles=1, finals_reached=1, podiums=1)
    keys = _keys(titles=3, finals_reached=3, podiums=3)
    assert "dynasty" in keys and "champion" not in keys


def test_finalist_and_podium():
    assert "finalist" in _keys(finals_reached=1, podiums=1)
    assert "podium" in _keys(podiums=1)


def test_streaks():
    assert "unstoppable" in _keys(longest_win_streak=5, matches_played=8, wins=6)
    on_fire = _keys(longest_win_streak=3, matches_played=4, wins=3)
    assert "on_fire" in on_fire and "unstoppable" not in on_fire


def test_sharpshooter_and_volume():
    assert "sharpshooter" in _keys(matches_played=10, wins=7)
    assert "veteran" in _keys(matches_played=50, wins=20)
    assert "regular" in _keys(matches_played=10, wins=3)


def test_no_badges_for_blank_slate():
    assert _keys() == set()


def test_achievements_endpoint_fresh_player(client, db):
    pid = make_approved_player(db, "fresh@example.com", "Fresh Face")
    resp = client.get(f"/api/v1/players/{pid}/achievements")
    assert resp.status_code == 200
    assert resp.json()["achievements"] == []
