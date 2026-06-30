import uuid

from app.db.models.player_profile import PlayerProfile
from tests.conftest import make_approved_player


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_exhibition(client, db, admin_token):
    players = [make_approved_player(db, f"ex_{i}@example.com", f"Ex{i}") for i in range(4)]
    resp = client.post(
        "/api/v1/exhibitions",
        json={
            "label": "Friday Friendly",
            "team_a": {"name": "Alpha", "player_ids": [players[0], players[1]]},
            "team_b": {"name": "Bravo", "player_ids": [players[2], players[3]]},
        },
        headers=_auth(admin_token),
    )
    assert resp.status_code == 201, resp.text
    return players, resp.json()


def test_create_exhibition(client, db, admin_token):
    players, match = _make_exhibition(client, db, admin_token)
    assert match["status"] == "SCHEDULED"
    assert {match["team_a_name"], match["team_b_name"]} == {"Alpha", "Bravo"}
    assert match["team_a_id"] and match["team_b_id"]


def test_exhibition_creation_requires_admin(client, db, admin_token):
    resp = client.post("/api/v1/exhibitions", json={}, headers={})
    assert resp.status_code in (401, 403)


def test_exhibition_hidden_from_tournament_lists(client, db, admin_token):
    _players, match = _make_exhibition(client, db, admin_token)
    listed = client.get("/api/v1/tournaments", headers=_auth(admin_token)).json()
    assert match["tournament_id"] not in [t["id"] for t in listed]
    # But it shows in the exhibition list.
    ex = client.get("/api/v1/exhibitions", headers=_auth(admin_token)).json()
    assert match["id"] in [m["id"] for m in ex]


def test_player_on_both_sides_rejected(client, db, admin_token):
    players = [make_approved_player(db, f"dup_{i}@example.com", f"Dup{i}") for i in range(2)]
    resp = client.post(
        "/api/v1/exhibitions",
        json={
            "team_a": {"name": "A", "player_ids": [players[0]]},
            "team_b": {"name": "B", "player_ids": [players[0]]},
        },
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422


def test_exhibition_target_points_21(client, db, admin_token):
    players = [make_approved_player(db, f"tp_{i}@example.com", f"Tp{i}") for i in range(2)]
    match = client.post(
        "/api/v1/exhibitions",
        json={
            "team_a": {"name": "A", "player_ids": [players[0]]},
            "team_b": {"name": "B", "player_ids": [players[1]]},
            "target_points": 21,
        },
        headers=_auth(admin_token),
    ).json()

    for _ in range(21):  # 11 wouldn't be enough to finish a game to 21
        client.post(
            f"/api/v1/matches/{match['id']}/points",
            json={"player_id": players[0], "skill": "smash", "kind": "WIN"},
            headers=_auth(admin_token),
        )
    version = client.get(f"/api/v1/matches/{match['id']}", headers=_auth(admin_token)).json()["version"]
    done = client.post(
        f"/api/v1/matches/{match['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    ).json()
    assert done["status"] == "COMPLETED"
    assert {done["team_a_score"], done["team_b_score"]} == {21, 0}


def test_exhibition_affects_elo_and_skills(client, db, admin_token):
    players, match = _make_exhibition(client, db, admin_token)
    winner, loser = players[0], players[2]

    for _ in range(11):  # winner takes 11 points by smash
        client.post(
            f"/api/v1/matches/{match['id']}/points",
            json={"player_id": winner, "skill": "smash", "kind": "WIN"},
            headers=_auth(admin_token),
        )
    version = client.get(f"/api/v1/matches/{match['id']}", headers=_auth(admin_token)).json()["version"]
    done = client.post(
        f"/api/v1/matches/{match['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    ).json()
    assert done["status"] == "COMPLETED"

    db.expire_all()
    w = db.get(PlayerProfile, uuid.UUID(winner))
    lo = db.get(PlayerProfile, uuid.UUID(loser))
    assert w.current_rating > 1000  # Elo rose for the winner
    assert lo.current_rating < 1000  # and fell for the loser

    skills = {s["key"]: s["value"] for s in client.get(f"/api/v1/players/{winner}/skills").json()["skills"]}
    assert skills["smash"] == 71  # play-derived, exactly like a tournament match
