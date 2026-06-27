from tests.conftest import register_player, verify_user_directly


def test_unauthenticated_is_401(client):
    resp = client.get("/api/v1/admin/players")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_player_cannot_access_admin(client, db):
    register_player(client)
    verify_user_directly(db, "player@example.com")
    tokens = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "playerpass1"}
    ).json()

    resp = client.get(
        "/api/v1/admin/players", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_admin_allowed(client, admin_token):
    resp = client.get(
        "/api/v1/admin/players", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200


def test_garbage_token_is_401(client):
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert resp.status_code == 401
