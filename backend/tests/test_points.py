from tests.conftest import setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _ready_match(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    teams = client.get(f"/api/v1/tournaments/{tid}/teams").json()
    team0 = next(t for t in teams if t["id"] == team_ids[0])
    smasher = team0["members"][0]["player_id"]
    match = client.get(f"/api/v1/tournaments/{tid}/matches").json()[0]
    return tid, team_ids, smasher, match


def _log(client, token, match_id, player_id, skill):
    return client.post(
        f"/api/v1/matches/{match_id}/points",
        json={"player_id": player_id, "skill": skill}, headers=_auth(token),
    )


def test_logging_points_derives_skill_on_completion(client, db, admin_token):
    tid, team_ids, smasher, m = _ready_match(client, db, admin_token)

    for _ in range(11):  # team0's smasher wins 11 points by smash
        _log(client, admin_token, m["id"], smasher, "smash")

    score = client.get(f"/api/v1/matches/{m['id']}/points").json()
    assert score["team_a"] + score["team_b"] == 11

    version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
    done = client.post(
        f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    )
    assert done.status_code == 200
    assert done.json()["status"] == "COMPLETED"
    assert done.json()["winner_team_id"] == team_ids[0]

    skills = {s["key"]: s["value"] for s in client.get(f"/api/v1/players/{smasher}/skills").json()["skills"]}
    # derived(11) = round(50 + 50*11/26) = 71; unused skills sit at baseline 50.
    assert skills["smash"] == 71
    assert skills["serve"] == 50


def test_undo_point(client, db, admin_token):
    _tid, _team_ids, smasher, m = _ready_match(client, db, admin_token)
    _log(client, admin_token, m["id"], smasher, "serve")
    after_undo = client.request(
        "DELETE", f"/api/v1/matches/{m['id']}/points/last", headers=_auth(admin_token)
    ).json()
    assert after_undo["team_a"] + after_undo["team_b"] == 0


def test_admin_override_is_not_overwritten_by_play(client, db, admin_token):
    tid, team_ids, smasher, m = _ready_match(client, db, admin_token)
    # Admin pins smash to 90.
    client.patch(
        f"/api/v1/admin/players/{smasher}/skills",
        json={"ratings": {"smash": 90}}, headers=_auth(admin_token),
    )
    for _ in range(11):
        _log(client, admin_token, m["id"], smasher, "smash")
    version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
    client.post(
        f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    )
    skills = {s["key"]: s["value"] for s in client.get(f"/api/v1/players/{smasher}/skills").json()["skills"]}
    assert skills["smash"] == 90  # pinned, not overwritten by play


def test_cannot_log_to_completed_match(client, db, admin_token):
    _tid, _team_ids, smasher, m = _ready_match(client, db, admin_token)
    for _ in range(11):
        _log(client, admin_token, m["id"], smasher, "smash")
    version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
    client.post(f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}", headers=_auth(admin_token))
    resp = _log(client, admin_token, m["id"], smasher, "smash")
    assert resp.status_code == 409
