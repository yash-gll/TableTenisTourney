"""API integration version of the required A/B/C/D/E leaderboard test (spec §11)."""

from tests.conftest import create_tournament, make_approved_player
from tests.test_leaderboard import ABCDE_RESULTS

# Lookup keyed by the unordered pair -> (first_name, first_score, second_score).
RESULT_LOOKUP = {frozenset((a, b)): (a, sa, sb) for a, b, sa, sb in ABCDE_RESULTS}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_abcde_leaderboard_via_api(client, db, admin_token):
    hdr = _auth(admin_token)
    t = create_tournament(client, admin_token, "ABCDE Cup")
    tid = t["id"]

    for idx, name in enumerate(["A", "B", "C", "D", "E"]):
        team_id = client.post(
            f"/api/v1/tournaments/{tid}/teams", json={"name": name}, headers=hdr
        ).json()["id"]
        for j in range(2):
            pid = make_approved_player(db, f"abcde_{idx}_{j}@example.com", f"{name}{j}")
            client.post(
                f"/api/v1/tournaments/{tid}/teams/{team_id}/members",
                json={"player_id": pid}, headers=hdr,
            )

    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_OPEN"}, headers=hdr)
    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_CLOSED"}, headers=hdr)
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=hdr)

    matches = client.get(f"/api/v1/tournaments/{tid}/matches").json()
    assert len(matches) == 10

    for m in matches:
        na, nb = m["team_a_name"], m["team_b_name"]
        first, fs, ss = RESULT_LOOKUP[frozenset((na, nb))]
        a_score, b_score = (fs, ss) if first == na else (ss, fs)
        resp = client.post(
            f"/api/v1/matches/{m['id']}/complete",
            json={"team_a_score": a_score, "team_b_score": b_score, "expected_version": m["version"]},
            headers=hdr,
        )
        assert resp.status_code == 200, resp.text

    lb = client.get(f"/api/v1/tournaments/{tid}/leaderboard").json()
    assert lb["group_complete"] is True
    order = [s["team_name"] for s in lb["standings"]]
    assert order == ["B", "D", "E", "A", "C"]

    top = lb["standings"][0]
    assert top["team_name"] == "B"
    assert (top["wins"], top["points_for"], top["points_against"], top["point_difference"]) == (
        3, 43, 31, 12,
    )
    assert top["qualification_status"] == "QUALIFIED"
