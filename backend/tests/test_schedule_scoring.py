from tests.conftest import setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_generate_schedule_creates_matches(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    resp = client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["match_count"] == 6

    matches = client.get(f"/api/v1/tournaments/{tid}/matches").json()
    assert len(matches) == 6
    assert all(m["status"] == "SCHEDULED" for m in matches)
    # Tournament moved to SCHEDULED.
    assert client.get(f"/api/v1/tournaments/{tid}", headers=_auth(admin_token)).json()["status"] == "SCHEDULED"


def test_schedule_idempotent(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    again = client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "SCHEDULE_ALREADY_GENERATED"


def test_complete_match_determines_winner(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    m = client.get(f"/api/v1/tournaments/{tid}/matches").json()[0]

    resp = client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": 11, "team_b_score": 7, "expected_version": m["version"]},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["winner_team_id"] == body["team_a_id"]
    assert body["version"] == m["version"] + 1


def test_invalid_score_rejected(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    m = client.get(f"/api/v1/tournaments/{tid}/matches").json()[0]
    resp = client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": 10, "team_b_score": 10, "expected_version": m["version"]},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_MATCH_SCORE"


def test_version_conflict(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    m = client.get(f"/api/v1/tournaments/{tid}/matches").json()[0]
    # First completion bumps the version.
    client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": 11, "team_b_score": 5, "expected_version": m["version"]},
        headers=_auth(admin_token),
    )
    # Second request with the stale version conflicts.
    stale = client.post(
        f"/api/v1/matches/{m['id']}/correct",
        json={"team_a_score": 11, "team_b_score": 6, "expected_version": m["version"], "reason": "x"},
        headers=_auth(admin_token),
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "MATCH_VERSION_CONFLICT"


def test_correction_changes_winner(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    m = client.get(f"/api/v1/tournaments/{tid}/matches").json()[0]
    done = client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": 11, "team_b_score": 5, "expected_version": m["version"]},
        headers=_auth(admin_token),
    ).json()
    assert done["winner_team_id"] == done["team_a_id"]

    corrected = client.post(
        f"/api/v1/matches/{m['id']}/correct",
        json={"team_a_score": 5, "team_b_score": 11, "expected_version": done["version"],
              "reason": "Scores entered reversed"},
        headers=_auth(admin_token),
    ).json()
    assert corrected["winner_team_id"] == corrected["team_b_id"]


def test_group_completes_when_all_done(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 4)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    matches = client.get(f"/api/v1/tournaments/{tid}/matches").json()
    for m in matches:
        client.post(
            f"/api/v1/matches/{m['id']}/complete",
            json={"team_a_score": 11, "team_b_score": 3, "expected_version": m["version"]},
            headers=_auth(admin_token),
        )
    status = client.get(f"/api/v1/tournaments/{tid}", headers=_auth(admin_token)).json()["status"]
    assert status == "GROUP_COMPLETE"
