from tests.conftest import make_approved_player, register_player


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_search_lists_approved_players_only(client, db):
    make_approved_player(db, "alice@example.com", "Alice Ace")
    make_approved_player(db, "bob@example.com", "Bob Smash")
    # A pending (unapproved) player should not appear.
    register_player(client, email="pending@example.com", display_name="Pending Pete")

    everyone = client.get("/api/v1/players").json()
    names = {p["display_name"] for p in everyone}
    assert "Alice Ace" in names and "Bob Smash" in names
    assert "Pending Pete" not in names


def test_search_filters_by_name(client, db):
    make_approved_player(db, "alice2@example.com", "Alice Ace")
    make_approved_player(db, "bob2@example.com", "Bob Smash")
    resp = client.get("/api/v1/players", params={"search": "smash"})
    names = [p["display_name"] for p in resp.json()]
    assert names == ["Bob Smash"]


def test_public_profile_has_stats_and_skills(client, db):
    pid = make_approved_player(db, "carol@example.com", "Carol Chop")
    profile = client.get(f"/api/v1/players/{pid}").json()
    assert profile["display_name"] == "Carol Chop"
    assert profile["current_rating"] == 1000
    assert profile["stats"] == {
        "matches_played": 0, "wins": 0, "losses": 0, "win_pct": 0.0,
        "tournaments_played": 0, "tournament_wins": 0,
    }
    # Skills available via the skills endpoint, no email anywhere.
    skills = client.get(f"/api/v1/players/{pid}/skills").json()
    assert [s["key"] for s in skills["skills"]][0] == "serve"
    assert "email" not in profile and "carol@example.com" not in str(profile)


def test_me_not_captured_by_player_id_route(client, db):
    # /players/me must still resolve to the authed profile, not {player_id}.
    register_player(client, email="meuser@example.com", display_name="Me User")
    from tests.conftest import verify_user_directly

    verify_user_directly(db, "meuser@example.com")
    token = client.post(
        "/api/v1/auth/login", json={"email": "meuser@example.com", "password": "playerpass1"}
    ).json()["access_token"]
    me = client.get("/api/v1/players/me", headers=_auth(token))
    assert me.status_code == 200
    assert me.json()["email"] == "meuser@example.com"
