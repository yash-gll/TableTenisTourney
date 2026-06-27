from tests.conftest import setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _matches(client, tid):
    return client.get(f"/api/v1/tournaments/{tid}/matches").json()


def _by_stage(client, tid, stage):
    return next(m for m in _matches(client, tid) if m["stage"] == stage)


def _complete(client, token, m, a, b):
    return client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": a, "team_b_score": b, "expected_version": m["version"]},
        headers=_auth(token),
    )


def _play_group_ordered(client, token, tid, team_ids):
    """Complete all group matches so team_ids[0] finishes rank 1 ... rank 4
    (lower index always wins)."""
    rank = {tid_: i for i, tid_ in enumerate(team_ids)}
    for m in _matches(client, tid):
        if m["stage"] != "GROUP":
            continue
        if rank[m["team_a_id"]] < rank[m["team_b_id"]]:
            _complete(client, token, m, 11, 0)
        else:
            _complete(client, token, m, 0, 11)


def _ready_bracket(client, db, token):
    setup = setup_closed_tournament(client, db, token, 4)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(token))
    _play_group_ordered(client, token, tid, team_ids)
    return tid, team_ids


def test_generate_bracket_seeds_qf1_qf2(client, db, admin_token):
    tid, team_ids = _ready_bracket(client, db, admin_token)
    resp = client.post(f"/api/v1/tournaments/{tid}/bracket/generate", headers=_auth(admin_token))
    assert resp.status_code == 200, resp.text
    by_stage = {m["stage"]: m for m in resp.json()["matches"]}
    # rank1=team0, rank2=team1, rank3=team2, rank4=team3
    assert {by_stage["QF1"]["team_a_id"], by_stage["QF1"]["team_b_id"]} == {team_ids[0], team_ids[1]}
    assert {by_stage["QF2"]["team_a_id"], by_stage["QF2"]["team_b_id"]} == {team_ids[2], team_ids[3]}
    assert by_stage["QF3"]["status"] == "WAITING_FOR_TEAMS"
    assert by_stage["FINAL"]["status"] == "WAITING_FOR_TEAMS"
    # Tournament advanced.
    assert client.get(f"/api/v1/tournaments/{tid}", headers=_auth(admin_token)).json()["status"] == "QUALIFIERS_IN_PROGRESS"


def test_generate_requires_group_complete(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    resp = client.post(f"/api/v1/tournaments/{tid}/bracket/generate", headers=_auth(admin_token))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] in ("GROUP_STAGE_INCOMPLETE",)


def test_full_propagation_to_champion(client, db, admin_token):
    tid, team_ids = _ready_bracket(client, db, admin_token)
    client.post(f"/api/v1/tournaments/{tid}/bracket/generate", headers=_auth(admin_token))

    qf1 = _by_stage(client, tid, "QF1")
    # team0 (rank1) beats team1 (rank2)
    a, b = (11, 0) if qf1["team_a_id"] == team_ids[0] else (0, 11)
    _complete(client, admin_token, qf1, a, b)

    # QF1 winner -> Final TEAM_A; QF1 loser -> QF3 TEAM_B
    final = _by_stage(client, tid, "FINAL")
    qf3 = _by_stage(client, tid, "QF3")
    assert final["team_a_id"] == team_ids[0]
    assert qf3["team_b_id"] == team_ids[1]

    qf2 = _by_stage(client, tid, "QF2")
    a, b = (11, 0) if qf2["team_a_id"] == team_ids[2] else (0, 11)
    _complete(client, admin_token, qf2, a, b)
    qf3 = _by_stage(client, tid, "QF3")
    assert qf3["team_a_id"] == team_ids[2]  # QF2 winner
    assert qf3["status"] == "SCHEDULED"

    # QF3: team2 vs team1 — let team1 win
    a, b = (11, 0) if qf3["team_a_id"] == team_ids[1] else (0, 11)
    _complete(client, admin_token, qf3, a, b)
    final = _by_stage(client, tid, "FINAL")
    assert final["team_b_id"] == team_ids[1]  # QF3 winner

    a, b = (11, 0) if final["team_a_id"] == team_ids[0] else (0, 11)
    _complete(client, admin_token, final, a, b)

    bracket = client.get(f"/api/v1/tournaments/{tid}/bracket").json()
    places = {p["place"]: p["team_id"] for p in bracket["placements"]}
    assert places[1] == team_ids[0]   # champion
    assert places[2] == team_ids[1]   # runner-up
    assert places[3] == team_ids[2]   # QF3 loser
    assert places[4] == team_ids[3]   # QF2 loser
    assert client.get(f"/api/v1/tournaments/{tid}", headers=_auth(admin_token)).json()["status"] == "COMPLETED"


def test_correcting_qf1_updates_dependents_when_not_started(client, db, admin_token):
    tid, team_ids = _ready_bracket(client, db, admin_token)
    client.post(f"/api/v1/tournaments/{tid}/bracket/generate", headers=_auth(admin_token))
    qf1 = _by_stage(client, tid, "QF1")
    a, b = (11, 0) if qf1["team_a_id"] == team_ids[0] else (0, 11)
    done = _complete(client, admin_token, qf1, a, b).json()

    # Reverse the QF1 result; QF3/Final not started yet.
    ra, rb = (0, 11) if done["team_a_id"] == team_ids[0] else (11, 0)
    resp = client.post(
        f"/api/v1/matches/{qf1['id']}/correct",
        json={"team_a_score": ra, "team_b_score": rb, "expected_version": done["version"],
              "reason": "fix"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200
    final = _by_stage(client, tid, "FINAL")
    assert final["team_a_id"] == team_ids[1]  # new QF1 winner propagated


def test_correction_blocked_when_dependent_completed(client, db, admin_token):
    tid, team_ids = _ready_bracket(client, db, admin_token)
    client.post(f"/api/v1/tournaments/{tid}/bracket/generate", headers=_auth(admin_token))

    qf1 = _by_stage(client, tid, "QF1")
    a, b = (11, 0) if qf1["team_a_id"] == team_ids[0] else (0, 11)
    qf1_done = _complete(client, admin_token, qf1, a, b).json()
    qf2 = _by_stage(client, tid, "QF2")
    a, b = (11, 0) if qf2["team_a_id"] == team_ids[2] else (0, 11)
    _complete(client, admin_token, qf2, a, b)
    qf3 = _by_stage(client, tid, "QF3")
    _complete(client, admin_token, qf3, 11, 0)  # QF3 now COMPLETED (depends on QF1 loser)

    ra, rb = (0, 11) if qf1_done["team_a_id"] == team_ids[0] else (11, 0)
    blocked = client.post(
        f"/api/v1/matches/{qf1['id']}/correct",
        json={"team_a_score": ra, "team_b_score": rb, "expected_version": qf1_done["version"],
              "reason": "x", "reset_dependents": False},
        headers=_auth(admin_token),
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "DEPENDENT_MATCH_ALREADY_STARTED"

    # With reset_dependents the correction succeeds and downstream is reset.
    ok = client.post(
        f"/api/v1/matches/{qf1['id']}/correct",
        json={"team_a_score": ra, "team_b_score": rb, "expected_version": qf1_done["version"],
              "reason": "x", "reset_dependents": True},
        headers=_auth(admin_token),
    )
    assert ok.status_code == 200
    qf3_after = _by_stage(client, tid, "QF3")
    assert qf3_after["status"] in ("WAITING_FOR_TEAMS", "SCHEDULED")
    assert qf3_after["winner_team_id"] is None
