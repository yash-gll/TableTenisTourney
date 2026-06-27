from tests.conftest import make_approved_player


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_approval_initializes_skills(client, db, admin_token):
    from tests.conftest import register_player

    register_player(client, email="appr@example.com", display_name="Appr Player")
    pid = client.get(
        "/api/v1/admin/players?approval_status=PENDING", headers=_auth(admin_token)
    ).json()[0]["player_id"]
    # Before approval: unrated.
    before = client.get(f"/api/v1/players/{pid}/skills").json()
    assert all(s["value"] is None for s in before["skills"])
    # Approve → baseline 50 across the board.
    client.post(f"/api/v1/admin/players/{pid}/approve", headers=_auth(admin_token))
    after = client.get(f"/api/v1/players/{pid}/skills").json()
    assert all(s["value"] == 50 for s in after["skills"])


def test_skills_default_empty_and_public(client, db):
    pid = make_approved_player(db, "skilltest@example.com", "Skill Tester")
    resp = client.get(f"/api/v1/players/{pid}/skills")  # public, no auth
    assert resp.status_code == 200
    body = resp.json()
    assert [s["key"] for s in body["skills"]] == [
        "serve", "smash", "spin", "footwork", "consistency",
    ]
    assert all(s["value"] is None for s in body["skills"])


def test_admin_edits_skills(client, db, admin_token):
    pid = make_approved_player(db, "edit@example.com", "Edit Me")
    resp = client.patch(
        f"/api/v1/admin/players/{pid}/skills",
        json={"ratings": {"serve": 80, "smash": 65}},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200
    values = {s["key"]: s["value"] for s in resp.json()["skills"]}
    assert values["serve"] == 80 and values["smash"] == 65 and values["spin"] is None

    # Partial update merges (serve stays).
    client.patch(
        f"/api/v1/admin/players/{pid}/skills",
        json={"ratings": {"spin": 50}},
        headers=_auth(admin_token),
    )
    public = client.get(f"/api/v1/players/{pid}/skills").json()
    values = {s["key"]: s["value"] for s in public["skills"]}
    assert values["serve"] == 80 and values["spin"] == 50


def test_skill_validation(client, db, admin_token):
    pid = make_approved_player(db, "bad@example.com", "Bad Skills")
    over = client.patch(
        f"/api/v1/admin/players/{pid}/skills",
        json={"ratings": {"serve": 150}}, headers=_auth(admin_token),
    )
    assert over.status_code == 422 and over.json()["error"]["code"] == "INVALID_SKILL_RATING"

    unknown = client.patch(
        f"/api/v1/admin/players/{pid}/skills",
        json={"ratings": {"teleport": 50}}, headers=_auth(admin_token),
    )
    assert unknown.status_code == 422


def test_skills_edit_requires_admin(client, db):
    pid = make_approved_player(db, "noauth@example.com", "No Auth")
    resp = client.patch(f"/api/v1/admin/players/{pid}/skills", json={"ratings": {"serve": 10}})
    assert resp.status_code == 401


def test_player_sees_own_skills_in_profile(client, db, admin_token):
    pid = make_approved_player(db, "ownskills@example.com", "Owner")
    client.patch(
        f"/api/v1/admin/players/{pid}/skills",
        json={"ratings": {"footwork": 90}}, headers=_auth(admin_token),
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": "ownskills@example.com", "password": "playerpass1"}
    ).json()["access_token"]
    me = client.get("/api/v1/players/me", headers=_auth(token)).json()
    assert me["skill_ratings"]["footwork"] == 90
