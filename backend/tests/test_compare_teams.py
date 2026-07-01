from tests.conftest import setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _pair(client, tid, team_id):
    teams = client.get(f"/api/v1/tournaments/{tid}/teams").json()
    team = next(t for t in teams if t["id"] == team_id)
    return [m["player_id"] for m in team["members"]]


def _play_group(client, admin_token, tid):
    """Play every scheduled match to completion (team A always wins by smash)."""
    matches = client.get(f"/api/v1/tournaments/{tid}/matches").json()
    for m in matches:
        winner = _pair(client, tid, m["team_a_id"])[0]
        for _ in range(11):
            client.post(
                f"/api/v1/matches/{m['id']}/points",
                json={"player_id": winner, "skill": "smash", "kind": "WIN"},
                headers=_auth(admin_token),
            )
        version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
        client.post(
            f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}",
            headers=_auth(admin_token),
        )


def test_compare_teams_uses_pair_matches(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    pair_a = _pair(client, tid, team_ids[0])
    pair_b = _pair(client, tid, team_ids[1])
    _play_group(client, admin_token, tid)

    resp = client.post(
        "/api/v1/compare/teams",
        json={"team_a": pair_a, "team_b": pair_b},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Two teams, one match between them, team A won it.
    assert data["team_a"]["stats"]["matches_played"] == 1
    assert data["team_a"]["stats"]["wins"] == 1
    assert data["team_b"]["stats"]["losses"] == 1
    assert data["head_to_head"] == {"meetings": 1, "a_wins": 1, "b_wins": 0}
    assert len(data["team_a"]["skills"]) == 5


def test_compare_identical_teams_rejected(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    pair_a = _pair(client, tid, team_ids[0])
    resp = client.post(
        "/api/v1/compare/teams",
        json={"team_a": pair_a, "team_b": pair_a},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_COMPARISON"


def test_compare_requires_auth(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    pair_a = _pair(client, tid, team_ids[0])
    pair_b = _pair(client, tid, team_ids[1])
    resp = client.post("/api/v1/compare/teams", json={"team_a": pair_a, "team_b": pair_b})
    assert resp.status_code in (401, 403)
