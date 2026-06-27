from tests.conftest import create_tournament, make_approved_player


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _open_tournament(client, admin_token) -> str:
    t = create_tournament(client, admin_token, "Open Cup")
    tid = t["id"]
    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_OPEN"},
                headers=_auth(admin_token))
    return tid


def _player_token(client, db, email="reg@example.com", name="Reg Player") -> str:
    make_approved_player(db, email, name)
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": "playerpass1"}
    ).json()["access_token"]


def test_player_can_request_and_appears_to_admin(client, db, admin_token):
    tid = _open_tournament(client, admin_token)
    ptoken = _player_token(client, db)

    resp = client.post(f"/api/v1/tournaments/{tid}/registrations", json={"note": "Pick me"},
                       headers=_auth(ptoken))
    assert resp.status_code == 201
    assert resp.json()["status"] == "REQUESTED"

    # Player's own status.
    mine = client.get(f"/api/v1/tournaments/{tid}/registrations/me", headers=_auth(ptoken)).json()
    assert mine["status"] == "REQUESTED"

    # Admin sees the request.
    listing = client.get(f"/api/v1/tournaments/{tid}/registrations", headers=_auth(admin_token)).json()
    assert len(listing) == 1 and listing[0]["display_name"] == "Reg Player"


def test_duplicate_request_rejected(client, db, admin_token):
    tid = _open_tournament(client, admin_token)
    ptoken = _player_token(client, db)
    client.post(f"/api/v1/tournaments/{tid}/registrations", json={}, headers=_auth(ptoken))
    again = client.post(f"/api/v1/tournaments/{tid}/registrations", json={}, headers=_auth(ptoken))
    assert again.status_code == 409 and again.json()["error"]["code"] == "ALREADY_REGISTERED"


def test_request_only_when_open(client, db, admin_token):
    t = create_tournament(client, admin_token, "Draft Cup")  # stays DRAFT
    ptoken = _player_token(client, db)
    resp = client.post(f"/api/v1/tournaments/{t['id']}/registrations", json={}, headers=_auth(ptoken))
    assert resp.status_code == 409 and resp.json()["error"]["code"] == "REGISTRATION_NOT_OPEN"


def test_admin_accept_and_player_withdraw_then_reapply(client, db, admin_token):
    tid = _open_tournament(client, admin_token)
    ptoken = _player_token(client, db)
    pid = client.post(f"/api/v1/tournaments/{tid}/registrations", json={}, headers=_auth(ptoken)) and \
        client.get(f"/api/v1/tournaments/{tid}/registrations", headers=_auth(admin_token)).json()[0]["player_id"]

    accept = client.post(f"/api/v1/tournaments/{tid}/registrations/{pid}/accept", headers=_auth(admin_token))
    assert accept.status_code == 200 and accept.json()["status"] == "ACCEPTED"

    # Withdraw, then re-request is allowed.
    client.request("DELETE", f"/api/v1/tournaments/{tid}/registrations/me", headers=_auth(ptoken))
    assert client.get(f"/api/v1/tournaments/{tid}/registrations/me", headers=_auth(ptoken)).json()["status"] == "WITHDRAWN"
    re = client.post(f"/api/v1/tournaments/{tid}/registrations", json={}, headers=_auth(ptoken))
    assert re.status_code == 201 and re.json()["status"] == "REQUESTED"


def test_open_tournament_visible_in_player_list(client, db, admin_token):
    tid = _open_tournament(client, admin_token)
    ptoken = _player_token(client, db)
    listed = client.get("/api/v1/tournaments", headers=_auth(ptoken)).json()
    assert any(t["id"] == tid for t in listed)
