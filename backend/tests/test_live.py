import uuid

from app.db.models.enums import TournamentVisibility
from app.db.models.tournament import Tournament
from tests.conftest import make_approved_player, setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _start_first_match(client, admin_token, tid):
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    match = client.get(f"/api/v1/tournaments/{tid}/matches", headers=_auth(admin_token)).json()[0]
    client.post(f"/api/v1/matches/{match['id']}/start", headers=_auth(admin_token))
    return match["id"]


def test_live_requires_auth(client, db, admin_token):
    assert client.get("/api/v1/live").status_code in (401, 403)


def test_live_shows_exhibition_and_tournament(client, db, admin_token):
    # An exhibition, auto-started by logging its first point.
    players = [make_approved_player(db, f"lv_{i}@example.com", f"Lv{i}") for i in range(2)]
    ex = client.post(
        "/api/v1/exhibitions",
        json={
            "team_a": {"name": "Alpha", "player_ids": [players[0]]},
            "team_b": {"name": "Bravo", "player_ids": [players[1]]},
        },
        headers=_auth(admin_token),
    ).json()
    client.post(
        f"/api/v1/matches/{ex['id']}/points",
        json={"player_id": players[0], "skill": "smash", "kind": "WIN"},
        headers=_auth(admin_token),
    )

    # A regular tournament with a started match.
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tmatch = _start_first_match(client, admin_token, setup["tournament_id"])

    live = client.get("/api/v1/live", headers=_auth(admin_token)).json()
    by_id = {m["id"]: m for m in live}
    assert ex["id"] in by_id and by_id[ex["id"]]["is_exhibition"] is True
    assert by_id[ex["id"]]["context_name"] == "Exhibition"
    assert by_id[ex["id"]]["team_a_score"] + by_id[ex["id"]]["team_b_score"] == 1
    assert tmatch in by_id and by_id[tmatch]["is_exhibition"] is False


def test_live_hides_private_tournaments(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid = setup["tournament_id"]
    t = db.get(Tournament, uuid.UUID(tid))
    t.visibility = TournamentVisibility.PRIVATE
    db.commit()

    tmatch = _start_first_match(client, admin_token, tid)
    live = client.get("/api/v1/live", headers=_auth(admin_token)).json()
    assert tmatch not in [m["id"] for m in live]
