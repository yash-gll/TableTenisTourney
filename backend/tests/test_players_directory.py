from tests.conftest import setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_directory_includes_basic_stats(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    teams = client.get(f"/api/v1/tournaments/{tid}/teams").json()
    winner_team = next(t for t in teams if t["id"] == team_ids[0])
    loser_team = next(t for t in teams if t["id"] == team_ids[1])
    winner = winner_team["members"][0]["player_id"]
    loser = loser_team["members"][0]["player_id"]

    match = client.get(f"/api/v1/tournaments/{tid}/matches").json()[0]
    for _ in range(11):
        client.post(
            f"/api/v1/matches/{match['id']}/points",
            json={"player_id": winner, "skill": "smash", "kind": "WIN"},
            headers=_auth(admin_token),
        )
    version = client.get(f"/api/v1/matches/{match['id']}").json()["version"]
    client.post(
        f"/api/v1/matches/{match['id']}/points/complete?expected_version={version}",
        headers=_auth(admin_token),
    )

    directory = {p["player_id"]: p for p in client.get("/api/v1/players").json()}
    assert directory[winner]["matches_played"] == 1
    assert directory[winner]["win_pct"] == 100.0
    assert directory[loser]["matches_played"] == 1
    assert directory[loser]["win_pct"] == 0.0
    assert directory[loser]["losses"] == 1
    # Rally-level: the smasher decided 11 rallies, all wins.
    assert directory[winner]["rallies_played"] == 11
    assert directory[winner]["rally_win_pct"] == 100.0
    assert directory[loser]["rallies_played"] == 0
    # Average match points: winner 11 scored / 0 conceded, loser the reverse.
    assert directory[winner]["avg_points_for"] == 11.0
    assert directory[winner]["avg_points_against"] == 0.0
    assert directory[loser]["avg_points_for"] == 0.0
    assert directory[loser]["avg_points_against"] == 11.0


def test_teammates_best_and_worst(client, db, admin_token):
    # A 3-team tournament: everyone plays everyone, so team1's pair share matches.
    setup = setup_closed_tournament(client, db, admin_token, 3)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    teams = {t["id"]: t for t in client.get(f"/api/v1/tournaments/{tid}/teams").json()}
    # Complete every match; team_ids[0] always wins.
    matches = client.get(f"/api/v1/tournaments/{tid}/matches").json()
    for m in matches:
        winner_team = team_ids[0] if team_ids[0] in (m["team_a_id"], m["team_b_id"]) else m["team_a_id"]
        p = teams[winner_team]["members"][0]["player_id"]
        for _ in range(11):
            client.post(
                f"/api/v1/matches/{m['id']}/points",
                json={"player_id": p, "skill": "smash", "kind": "WIN"},
                headers=_auth(admin_token),
            )
        version = client.get(f"/api/v1/matches/{m['id']}").json()["version"]
        client.post(
            f"/api/v1/matches/{m['id']}/points/complete?expected_version={version}",
            headers=_auth(admin_token),
        )

    # A player on team1 has exactly one partner (their teammate).
    p1 = teams[team_ids[0]]["members"][0]["player_id"]
    partner = teams[team_ids[0]]["members"][1]["player_id"]
    mates = client.get(f"/api/v1/players/{p1}/teammates").json()["teammates"]
    assert [m["player_id"] for m in mates] == [partner]
    assert mates[0]["win_pct"] == 100.0  # team1 won all its matches
