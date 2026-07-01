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


def _log(client, token, match_id, player_id, skill, kind="WIN"):
    return client.post(
        f"/api/v1/matches/{match_id}/points",
        json={"player_id": player_id, "skill": skill, "kind": kind}, headers=_auth(token),
    )


def _player_on(client, tid, team_id):
    teams = client.get(f"/api/v1/tournaments/{tid}/teams").json()
    return next(t for t in teams if t["id"] == team_id)["members"][0]["player_id"]


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


def test_faults_score_opponent_and_lower_skill(client, db, admin_token):
    tid, team_ids, _smasher, m = _ready_match(client, db, admin_token)
    faulter = _player_on(client, tid, team_ids[1])  # a player on team B

    for _ in range(11):  # 11 serve faults by team B -> 11 points to team A
        _log(client, admin_token, m["id"], faulter, "serve_net", kind="FAULT")

    version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
    done = client.post(
        f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    ).json()
    assert done["winner_team_id"] == team_ids[0]  # opponent of the faulting team

    skills = {s["key"]: s["value"] for s in client.get(f"/api/v1/players/{faulter}/skills").json()["skills"]}
    # derived(wins=0, errors=11) = round(50 - 50*11/26) = 29; faults map to serve.
    assert skills["serve"] == 29


def test_live_score_visible_on_match_row(client, db, admin_token):
    tid, _team_ids, smasher, m = _ready_match(client, db, admin_token)
    for _ in range(3):
        _log(client, admin_token, m["id"], smasher, "smash")
    # The running tally is mirrored onto the match row so all viewers see it live.
    match = client.get(f"/api/v1/matches/{m['id']}").json()
    assert (match["team_a_score"] or 0) + (match["team_b_score"] or 0) == 3
    assert match["status"] == "IN_PROGRESS"


def test_forced_error_credits_forcer_and_debits_errer(client, db, admin_token):
    tid, team_ids, _smasher, m = _ready_match(client, db, admin_token)
    errer = _player_on(client, tid, team_ids[1])   # team B errs
    forcer = _player_on(client, tid, team_ids[0])  # team A forced it

    for _ in range(11):  # 11 forced errors -> 11 points to team A
        client.post(
            f"/api/v1/matches/{m['id']}/points",
            json={
                "player_id": errer, "skill": "hit_net", "kind": "FAULT",
                "forced_by": forcer, "forcer_skill": "smash",
            },
            headers=_auth(admin_token),
        )
    score = client.get(f"/api/v1/matches/{m['id']}/points").json()
    assert score["team_a"] + score["team_b"] == 11  # still one point per rally

    version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
    done = client.post(
        f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    ).json()
    assert done["winner_team_id"] == team_ids[0]

    forcer_skills = {s["key"]: s["value"] for s in client.get(f"/api/v1/players/{forcer}/skills").json()["skills"]}
    errer_skills = {s["key"]: s["value"] for s in client.get(f"/api/v1/players/{errer}/skills").json()["skills"]}
    assert forcer_skills["smash"] == 71   # forcer credited (wins=11)
    assert errer_skills["consistency"] == 29  # errer debited (hit_net -> consistency)


def test_forcer_must_be_opponent(client, db, admin_token):
    tid, team_ids, _s, m = _ready_match(client, db, admin_token)
    errer = _player_on(client, tid, team_ids[1])
    teammate = client.get(f"/api/v1/tournaments/{tid}/teams").json()
    partner = next(t for t in teammate if t["id"] == team_ids[1])["members"][1]["player_id"]
    resp = client.post(
        f"/api/v1/matches/{m['id']}/points",
        json={
            "player_id": errer, "skill": "hit_net", "kind": "FAULT",
            "forced_by": partner, "forcer_skill": "smash",  # partner, not an opponent
        },
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422


def test_set_serve_pairing(client, db, admin_token):
    tid, team_ids, _s, m = _ready_match(client, db, admin_token)
    a = _player_on(client, tid, team_ids[0])
    b = _player_on(client, tid, team_ids[1])
    resp = client.put(
        f"/api/v1/matches/{m['id']}/serve-pairing",
        json={"pairing": {a: b, b: a}, "first_server_id": a},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["serve_pairing"] == {a: b, b: a}
    assert resp.json()["first_server_id"] == a


def test_finish_from_points_leader_wins_early(client, db, admin_token):
    tid, team_ids, smasher, m = _ready_match(client, db, admin_token)
    # Stop at 5-0 (well short of 11) — admin ends it, leader wins.
    for _ in range(5):
        _log(client, admin_token, m["id"], smasher, "smash")
    version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
    done = client.post(
        f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    )
    assert done.status_code == 200
    assert done.json()["winner_team_id"] == team_ids[0]


def test_finish_from_points_rejects_tie(client, db, admin_token):
    tid, team_ids, smasher, m = _ready_match(client, db, admin_token)
    other = _player_on(client, tid, team_ids[1])
    _log(client, admin_token, m["id"], smasher, "smash")
    _log(client, admin_token, m["id"], other, "smash")  # 1-1
    version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
    resp = client.post(
        f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422


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
