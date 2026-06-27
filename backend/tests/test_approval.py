from app.db.models.audit_log import AuditLog
from tests.conftest import register_player, verify_user_directly


def _pending_player_id(client, admin_token) -> str:
    resp = client.get(
        "/api/v1/admin/players?approval_status=PENDING",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    players = resp.json()
    assert len(players) == 1
    return players[0]["player_id"]


def test_approve_sets_status_and_writes_audit(client, db, admin_token):
    register_player(client)
    player_id = _pending_player_id(client, admin_token)

    resp = client.post(
        f"/api/v1/admin/players/{player_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "APPROVED"

    audit = db.query(AuditLog).filter(AuditLog.action == "player.approve").all()
    assert len(audit) == 1
    assert audit[0].entity_id == player_id


def test_reject_requires_reason(client, admin_token):
    register_player(client)
    player_id = _pending_player_id(client, admin_token)

    # Missing reason -> validation error.
    resp = client.post(
        f"/api/v1/admin/players/{player_id}/reject",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422

    resp = client.post(
        f"/api/v1/admin/players/{player_id}/reject",
        json={"reason": "Incomplete profile"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "REJECTED"
    assert resp.json()["approval_reason"] == "Incomplete profile"


def test_suspend_then_restore(client, db, admin_token):
    register_player(client)
    verify_user_directly(db, "player@example.com")
    player_id = _pending_player_id(client, admin_token)

    client.post(
        f"/api/v1/admin/players/{player_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    suspend = client.post(
        f"/api/v1/admin/players/{player_id}/suspend",
        json={"reason": "Code of conduct"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert suspend.status_code == 200
    assert suspend.json()["approval_status"] == "SUSPENDED"

    restore = client.post(
        f"/api/v1/admin/players/{player_id}/restore",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert restore.status_code == 200
    assert restore.json()["approval_status"] == "APPROVED"


def test_list_filter_by_status(client, admin_token):
    register_player(client, email="a@example.com", display_name="A")
    register_player(client, email="b@example.com", display_name="B")
    pending = client.get(
        "/api/v1/admin/players?approval_status=PENDING",
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    assert len(pending) == 2

    approved = client.get(
        "/api/v1/admin/players?approval_status=APPROVED",
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    # Only the admin's own profile is APPROVED.
    assert all(p["approval_status"] == "APPROVED" for p in approved)
