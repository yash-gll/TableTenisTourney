from tests.conftest import (
    create_tournament,
    make_approved_player,
    register_player,
    setup_closed_tournament,
)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _new_team(client, admin_token, tid, name="Aces"):
    return client.post(
        f"/api/v1/tournaments/{tid}/teams", json={"name": name}, headers=_auth(admin_token)
    )


def test_create_team_and_list(client, admin_token):
    t = create_tournament(client, admin_token)
    resp = _new_team(client, admin_token, t["id"])
    assert resp.status_code == 201
    assert resp.json()["is_complete"] is False

    teams = client.get(f"/api/v1/tournaments/{t['id']}/teams").json()
    assert len(teams) == 1


def test_duplicate_team_name_rejected(client, admin_token):
    t = create_tournament(client, admin_token)
    _new_team(client, admin_token, t["id"], "Dupes")
    resp = _new_team(client, admin_token, t["id"], "Dupes")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "TEAM_NAME_TAKEN"


def test_add_two_members_completes_team(client, db, admin_token):
    t = create_tournament(client, admin_token)
    team_id = _new_team(client, admin_token, t["id"]).json()["id"]
    p1 = make_approved_player(db, "p1@example.com", "Alice Ace")
    p2 = make_approved_player(db, "p2@example.com", "Bob Smash")

    client.post(f"/api/v1/tournaments/{t['id']}/teams/{team_id}/members",
                json={"player_id": p1}, headers=_auth(admin_token))
    resp = client.post(f"/api/v1/tournaments/{t['id']}/teams/{team_id}/members",
                       json={"player_id": p2}, headers=_auth(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_complete"] is True
    assert len(body["members"]) == 2
    assert body["average_rating"] == 1000.0
    # No email leaked in public-safe member payload.
    assert "email" not in resp.text.lower()


def test_third_member_rejected(client, db, admin_token):
    t = create_tournament(client, admin_token)
    team_id = _new_team(client, admin_token, t["id"]).json()["id"]
    for i in range(2):
        pid = make_approved_player(db, f"full{i}@example.com", f"Player {i}")
        client.post(f"/api/v1/tournaments/{t['id']}/teams/{team_id}/members",
                    json={"player_id": pid}, headers=_auth(admin_token))
    pid3 = make_approved_player(db, "third@example.com", "Third Wheel")
    resp = client.post(f"/api/v1/tournaments/{t['id']}/teams/{team_id}/members",
                       json={"player_id": pid3}, headers=_auth(admin_token))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "TEAM_ALREADY_FULL"


def test_non_approved_player_rejected(client, admin_token):
    t = create_tournament(client, admin_token)
    team_id = _new_team(client, admin_token, t["id"]).json()["id"]
    # Register a PENDING player and find its id via the admin list.
    register_player(client, email="pending@example.com", display_name="Pending Pete")
    pending = client.get("/api/v1/admin/players?approval_status=PENDING",
                         headers=_auth(admin_token)).json()
    pid = pending[0]["player_id"]
    resp = client.post(f"/api/v1/tournaments/{t['id']}/teams/{team_id}/members",
                       json={"player_id": pid}, headers=_auth(admin_token))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "PLAYER_NOT_APPROVED"


def test_player_cannot_be_on_two_teams(client, db, admin_token):
    t = create_tournament(client, admin_token)
    team_a = _new_team(client, admin_token, t["id"], "A").json()["id"]
    team_b = _new_team(client, admin_token, t["id"], "B").json()["id"]
    pid = make_approved_player(db, "dual@example.com", "Dual Player")

    client.post(f"/api/v1/tournaments/{t['id']}/teams/{team_a}/members",
                json={"player_id": pid}, headers=_auth(admin_token))
    resp = client.post(f"/api/v1/tournaments/{t['id']}/teams/{team_b}/members",
                       json={"player_id": pid}, headers=_auth(admin_token))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "PLAYER_ALREADY_ON_TEAM"


def test_remove_member(client, db, admin_token):
    t = create_tournament(client, admin_token)
    team_id = _new_team(client, admin_token, t["id"]).json()["id"]
    pid = make_approved_player(db, "rm@example.com", "Remove Me")
    client.post(f"/api/v1/tournaments/{t['id']}/teams/{team_id}/members",
                json={"player_id": pid}, headers=_auth(admin_token))
    resp = client.request("DELETE", f"/api/v1/tournaments/{t['id']}/teams/{team_id}/members/{pid}",
                          headers=_auth(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()["members"]) == 0


def test_roster_locked_after_registration_closed(client, admin_token):
    t = create_tournament(client, admin_token)
    tid = t["id"]
    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_OPEN"},
                headers=_auth(admin_token))
    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_CLOSED"},
                headers=_auth(admin_token))
    resp = _new_team(client, admin_token, tid, "TooLate")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "TOURNAMENT_NOT_EDITABLE"


def test_rename_team_allowed_during_live_tournament(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid = setup["tournament_id"]
    team_id = setup["team_ids"][0]
    # Start the tournament (schedule generated -> SCHEDULED, rosters locked).
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))

    # Renaming is allowed mid-tournament...
    rename = client.patch(
        f"/api/v1/tournaments/{tid}/teams/{team_id}",
        json={"name": "Renamed Live"}, headers=_auth(admin_token),
    )
    assert rename.status_code == 200
    assert rename.json()["name"] == "Renamed Live"

    # ...but roster changes are still locked.
    pid = make_approved_player(db, "latecomer@example.com", "Late Comer")
    add = client.post(
        f"/api/v1/tournaments/{tid}/teams/{team_id}/members",
        json={"player_id": pid}, headers=_auth(admin_token),
    )
    assert add.status_code == 409
    assert add.json()["error"]["code"] == "TOURNAMENT_NOT_EDITABLE"


def test_team_create_requires_admin(client, db, admin_token):
    t = create_tournament(client, admin_token)
    # Guest cannot create a team.
    resp = client.post(f"/api/v1/tournaments/{t['id']}/teams", json={"name": "Nope"})
    assert resp.status_code == 401
