from tests.conftest import setup_closed_tournament
from tests.test_bracket_flow import _by_stage, _complete, _matches, _play_group_ordered


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _teams(client, tid):
    return client.get(f"/api/v1/tournaments/{tid}/teams").json()


def _ratings_by_player(client, tid):
    out = {}
    for team in _teams(client, tid):
        for m in team["members"]:
            out[m["player_id"]] = m["current_rating"]
    return out


def test_both_teammates_same_delta_and_change(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    before = _ratings_by_player(client, tid)

    m = next(mm for mm in _matches(client, tid) if mm["stage"] == "GROUP")
    _complete(client, admin_token, m, 11, 0)  # team A wins

    after = _ratings_by_player(client, tid)
    team_a_players = next(t for t in _teams(client, tid) if t["id"] == m["team_a_id"])["members"]
    deltas = [after[p["player_id"]] - before[p["player_id"]] for p in team_a_players]
    assert deltas[0] == deltas[1] and deltas[0] > 0  # same positive delta for both teammates


def _drive_to_completed(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    hdr = _auth(admin_token)
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=hdr)
    _play_group_ordered(client, admin_token, tid, team_ids)
    client.post(f"/api/v1/tournaments/{tid}/bracket/generate", headers=hdr)

    qf1 = _by_stage(client, tid, "QF1")
    _complete(client, admin_token, qf1, *(11, 0) if qf1["team_a_id"] == team_ids[0] else (0, 11))
    qf2 = _by_stage(client, tid, "QF2")
    _complete(client, admin_token, qf2, *(11, 0) if qf2["team_a_id"] == team_ids[2] else (0, 11))
    qf3 = _by_stage(client, tid, "QF3")
    _complete(client, admin_token, qf3, *(11, 0) if qf3["team_a_id"] == team_ids[1] else (0, 11))
    final = _by_stage(client, tid, "FINAL")
    _complete(client, admin_token, final, *(11, 0) if final["team_a_id"] == team_ids[0] else (0, 11))
    return tid, team_ids


def test_replay_matches_live(client, db, admin_token):
    tid, _ = _drive_to_completed(client, db, admin_token)
    before = _ratings_by_player(client, tid)
    # Recalculate (replay) should be idempotent vs the live-applied ratings.
    resp = client.post(
        "/api/v1/admin/ratings/recalculate", json={"tournament_id": tid}, headers=_auth(admin_token)
    )
    assert resp.status_code == 200
    assert _ratings_by_player(client, tid) == before


def test_champion_bonus_on_finalize(client, db, admin_token):
    tid, team_ids = _drive_to_completed(client, db, admin_token)
    before = _ratings_by_player(client, tid)

    champ_members = next(t for t in _teams(client, tid) if t["id"] == team_ids[0])["members"]
    runner_members = next(t for t in _teams(client, tid) if t["id"] == team_ids[1])["members"]

    resp = client.post(f"/api/v1/tournaments/{tid}/finalize", headers=_auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "FINALIZED"

    after = _ratings_by_player(client, tid)
    for p in champ_members:
        assert after[p["player_id"]] - before[p["player_id"]] == 50  # champion bonus
    for p in runner_members:
        assert after[p["player_id"]] - before[p["player_id"]] == 15  # runner-up, still positive


def test_finalize_then_history_and_reopen(client, db, admin_token):
    tid, team_ids = _drive_to_completed(client, db, admin_token)
    client.post(f"/api/v1/tournaments/{tid}/finalize", headers=_auth(admin_token))

    hist = client.get("/api/v1/history/tournaments").json()
    assert any(h["id"] == tid for h in hist)
    detail = client.get(f"/api/v1/history/tournaments/{tid}").json()
    assert detail["placements"][0]["place"] == 1
    lb = client.get(f"/api/v1/history/tournaments/{tid}/leaderboard").json()
    assert len(lb["standings"]) == 4

    before_reopen = _ratings_by_player(client, tid)
    reopen = client.post(f"/api/v1/tournaments/{tid}/reopen", headers=_auth(admin_token))
    assert reopen.status_code == 200
    assert reopen.json()["status"] == "COMPLETED"
    # Placement bonuses reverted: champion players drop by 50.
    after_reopen = _ratings_by_player(client, tid)
    champ_members = next(t for t in _teams(client, tid) if t["id"] == team_ids[0])["members"]
    for p in champ_members:
        assert before_reopen[p["player_id"]] - after_reopen[p["player_id"]] == 50
