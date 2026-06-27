from tests.conftest import make_approved_player, setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_form_and_rivals_after_a_match(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid, team_ids = setup["tournament_id"], setup["team_ids"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))

    teams = client.get(f"/api/v1/tournaments/{tid}/teams").json()
    team0 = next(t for t in teams if t["id"] == team_ids[0])
    pid = team0["members"][0]["player_id"]

    m = client.get(f"/api/v1/tournaments/{tid}/matches").json()[0]
    a, b = (11, 0) if m["team_a_id"] == team_ids[0] else (0, 11)  # team0 wins
    client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": a, "team_b_score": b, "expected_version": m["version"]},
        headers=_auth(admin_token),
    )

    profile = client.get(f"/api/v1/players/{pid}").json()
    assert profile["recent_form"] == ["W"]

    rivals = client.get(f"/api/v1/players/{pid}/rivals").json()["rivals"]
    assert len(rivals) == 2  # both opponents on the other team
    assert all(r["meetings"] == 1 and r["wins"] == 1 and r["losses"] == 0 for r in rivals)


def test_no_form_or_rivals_for_inactive_player(client, db):
    pid = make_approved_player(db, "idle@example.com", "Idle Ivan")
    assert client.get(f"/api/v1/players/{pid}").json()["recent_form"] == []
    assert client.get(f"/api/v1/players/{pid}/rivals").json()["rivals"] == []
