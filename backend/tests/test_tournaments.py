from tests.conftest import create_tournament, setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _player_token(client, email: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "playerpass1"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_player_sees_only_started_tournaments_they_are_in(client, db, admin_token):
    # Tournament A: player t2_0_0 is a participant.
    a = setup_closed_tournament(client, db, admin_token, 2)
    player_email = "t2_0_0@example.com"
    ptoken = _player_token(client, player_email)

    # Not started yet (REGISTRATION_CLOSED) -> not visible to the player.
    assert client.get("/api/v1/tournaments", headers=_auth(ptoken)).json() == []

    # Admin starts it (generates schedule).
    client.post(f"/api/v1/tournaments/{a['tournament_id']}/schedule/generate", headers=_auth(admin_token))
    visible = client.get("/api/v1/tournaments", headers=_auth(ptoken)).json()
    assert [t["id"] for t in visible] == [a["tournament_id"]]

    # Tournament B (different players), started, but the player is NOT in it.
    b = setup_closed_tournament(client, db, admin_token, 3)
    client.post(f"/api/v1/tournaments/{b['tournament_id']}/schedule/generate", headers=_auth(admin_token))
    visible_ids = {t["id"] for t in client.get("/api/v1/tournaments", headers=_auth(ptoken)).json()}
    assert a["tournament_id"] in visible_ids
    assert b["tournament_id"] not in visible_ids

    # Admin still sees everything.
    admin_ids = {t["id"] for t in client.get("/api/v1/tournaments", headers=_auth(admin_token)).json()}
    assert {a["tournament_id"], b["tournament_id"]} <= admin_ids


def test_create_and_list(client, admin_token):
    t = create_tournament(client, admin_token, "Spring Open")
    assert t["status"] == "DRAFT"
    assert t["is_editable"] is True
    assert t["target_points"] == 11 and t["win_by_two"] is False

    listed = client.get("/api/v1/tournaments").json()
    assert any(item["id"] == t["id"] for item in listed)


def test_create_requires_admin(client):
    # Guest
    resp = client.post("/api/v1/tournaments", json={"name": "X"})
    assert resp.status_code == 401


def test_private_hidden_from_guests(client, admin_token):
    resp = client.post(
        "/api/v1/tournaments",
        json={"name": "Secret", "visibility": "PRIVATE"},
        headers=_auth(admin_token),
    )
    tid = resp.json()["id"]

    # Guest cannot list or fetch it.
    guest_list = client.get("/api/v1/tournaments").json()
    assert all(item["id"] != tid for item in guest_list)
    assert client.get(f"/api/v1/tournaments/{tid}").status_code == 404

    # Admin can.
    assert client.get(f"/api/v1/tournaments/{tid}", headers=_auth(admin_token)).status_code == 200


def test_update_config_and_version_bump(client, admin_token):
    t = create_tournament(client, admin_token)
    resp = client.patch(
        f"/api/v1/tournaments/{t['id']}",
        json={"name": "Renamed", "scoring": {"target_points": 21, "win_by_two": True,
                                             "win_table_points": 3, "loss_table_points": 0}},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Renamed"
    assert body["target_points"] == 21 and body["win_by_two"] is True
    assert body["version"] == t["version"] + 1


def test_status_not_patchable_only_via_transition(client, admin_token):
    t = create_tournament(client, admin_token)
    # PATCH ignores any status field (schema has none); status stays DRAFT.
    resp = client.patch(
        f"/api/v1/tournaments/{t['id']}", json={"status": "COMPLETED"}, headers=_auth(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DRAFT"


def test_valid_and_invalid_transitions(client, admin_token):
    t = create_tournament(client, admin_token)
    tid = t["id"]

    ok = client.post(
        f"/api/v1/tournaments/{tid}/transition",
        json={"target": "REGISTRATION_OPEN"},
        headers=_auth(admin_token),
    )
    assert ok.status_code == 200 and ok.json()["status"] == "REGISTRATION_OPEN"

    # Jumping straight to a non-manual / illegal state is rejected.
    bad = client.post(
        f"/api/v1/tournaments/{tid}/transition",
        json={"target": "COMPLETED"},
        headers=_auth(admin_token),
    )
    assert bad.status_code == 409
    assert bad.json()["error"]["code"] == "INVALID_TOURNAMENT_TRANSITION"

    sched = client.post(
        f"/api/v1/tournaments/{tid}/transition",
        json={"target": "SCHEDULED"},
        headers=_auth(admin_token),
    )
    assert sched.status_code == 409  # scheduling is a Phase 3 action, not manual


def test_update_blocked_when_locked(client, admin_token):
    t = create_tournament(client, admin_token)
    tid = t["id"]
    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_OPEN"},
                headers=_auth(admin_token))
    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_CLOSED"},
                headers=_auth(admin_token))
    resp = client.patch(f"/api/v1/tournaments/{tid}", json={"name": "Nope"}, headers=_auth(admin_token))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "TOURNAMENT_NOT_EDITABLE"


def test_delete_tournament(client, admin_token):
    t = create_tournament(client, admin_token)
    resp = client.delete(f"/api/v1/tournaments/{t['id']}", headers=_auth(admin_token))
    assert resp.status_code == 204
    assert client.get(f"/api/v1/tournaments/{t['id']}", headers=_auth(admin_token)).status_code == 404
