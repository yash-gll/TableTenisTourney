import logging
import re

from tests.conftest import register_player, verify_user_directly


def _extract_token(caplog) -> str:
    # Return the most recently logged token (the buffer may hold earlier ones).
    found = None
    for record in caplog.records:
        m = re.search(r"token=([\w\-\.]+)", record.getMessage())
        if m:
            found = m.group(1)
    if found is None:
        raise AssertionError("no token logged")
    return found


def test_register_creates_pending_profile(client):
    register_player(client)
    # Cannot log in until verified.
    resp = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "playerpass1"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_auto_verify_lets_user_login_without_verification(client):
    from app.core.config import settings

    settings.auto_verify_email = True
    try:
        register_player(client, email="auto@example.com", display_name="Auto V")
        resp = client.post(
            "/api/v1/auth/login", json={"email": "auto@example.com", "password": "playerpass1"}
        )
        assert resp.status_code == 200  # logged in without an email-verify step
    finally:
        settings.auto_verify_email = False


def test_duplicate_email_rejected(client):
    register_player(client)
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "player@example.com", "password": "other1234", "display_name": "Dup"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_verify_email_flow_via_logged_token(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.auth"):
        register_player(client)
        token = _extract_token(caplog)

    resp = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200

    resp = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "playerpass1"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]


def test_invalid_verify_token(client):
    register_player(client)
    resp = client.post("/api/v1/auth/verify-email", json={"token": "not-a-real-token"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_TOKEN"


def test_login_and_me(client, db):
    register_player(client)
    verify_user_directly(db, "player@example.com")
    resp = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "playerpass1"}
    )
    tokens = resp.json()
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "player@example.com"
    assert me.json()["approval_status"] == "PENDING"


def test_refresh_rotates_and_old_token_invalid(client, db):
    register_player(client)
    verify_user_directly(db, "player@example.com")
    tokens = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "playerpass1"}
    ).json()

    first_refresh = tokens["refresh_token"]
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert rotated.status_code == 200

    # Old refresh token is now revoked.
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert reuse.status_code == 400


def test_logout_revokes_refresh(client, db):
    register_player(client)
    verify_user_directly(db, "player@example.com")
    tokens = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "playerpass1"}
    ).json()

    client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 400


def test_password_reset_round_trip(client, db, caplog):
    register_player(client)
    verify_user_directly(db, "player@example.com")

    with caplog.at_level(logging.INFO, logger="app.auth"):
        client.post("/api/v1/auth/forgot-password", json={"email": "player@example.com"})
        token = _extract_token(caplog)

    resp = client.post(
        "/api/v1/auth/reset-password", json={"token": token, "password": "brandnew123"}
    )
    assert resp.status_code == 200

    # Old password no longer works; new one does.
    old = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "playerpass1"}
    )
    assert old.status_code == 401
    new = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "brandnew123"}
    )
    assert new.status_code == 200


def test_password_hash_never_returned(client, db):
    register_player(client)
    verify_user_directly(db, "player@example.com")
    tokens = client.post(
        "/api/v1/auth/login", json={"email": "player@example.com", "password": "playerpass1"}
    ).json()
    me = client.get(
        "/api/v1/players/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert "password" not in me.text.lower()
