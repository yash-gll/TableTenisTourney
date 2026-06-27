from tests.conftest import make_approved_player, setup_closed_tournament


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _scheduled(client, db, admin_token):
    setup = setup_closed_tournament(client, db, admin_token, 2)
    tid = setup["tournament_id"]
    client.post(f"/api/v1/tournaments/{tid}/schedule/generate", headers=_auth(admin_token))
    match = client.get(f"/api/v1/tournaments/{tid}/matches").json()[0]
    return tid, match


def _predictor_token(client, db, email="predict@example.com"):
    make_approved_player(db, email, "Predictor")
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": "playerpass1"}
    ).json()["access_token"]


def test_predict_and_grade_on_completion(client, db, admin_token):
    tid, m = _scheduled(client, db, admin_token)
    ptoken = _predictor_token(client, db)

    # Predict team A to win.
    pred = client.post(
        f"/api/v1/matches/{m['id']}/predict",
        json={"winner_team_id": m["team_a_id"]}, headers=_auth(ptoken),
    )
    assert pred.status_code == 200
    assert pred.json()["is_correct"] is None  # not graded yet

    # Admin completes the match with team A winning.
    client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": 11, "team_b_score": 5, "expected_version": m["version"]},
        headers=_auth(admin_token),
    )

    mine = client.get(f"/api/v1/tournaments/{tid}/predictions/me", headers=_auth(ptoken)).json()
    assert mine[0]["is_correct"] is True

    board = client.get(f"/api/v1/tournaments/{tid}/predictions/leaderboard").json()
    assert board[0]["display_name"] == "Predictor"
    assert board[0]["points"] == 1 and board[0]["correct"] == 1 and board[0]["total"] == 1


def test_pick_is_locked_once_made(client, db, admin_token):
    _tid, m = _scheduled(client, db, admin_token)
    ptoken = _predictor_token(client, db)
    first = client.post(
        f"/api/v1/matches/{m['id']}/predict",
        json={"winner_team_id": m["team_a_id"]}, headers=_auth(ptoken),
    )
    assert first.status_code == 200
    # Trying to change it (to the other team or the same) is rejected.
    change = client.post(
        f"/api/v1/matches/{m['id']}/predict",
        json={"winner_team_id": m["team_b_id"]}, headers=_auth(ptoken),
    )
    assert change.status_code == 409 and change.json()["error"]["code"] == "PREDICTION_LOCKED"


def test_cannot_predict_completed_match(client, db, admin_token):
    tid, m = _scheduled(client, db, admin_token)
    ptoken = _predictor_token(client, db)
    client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": 11, "team_b_score": 5, "expected_version": m["version"]},
        headers=_auth(admin_token),
    )
    resp = client.post(
        f"/api/v1/matches/{m['id']}/predict",
        json={"winner_team_id": m["team_a_id"]}, headers=_auth(ptoken),
    )
    assert resp.status_code == 409 and resp.json()["error"]["code"] == "MATCH_NOT_PREDICTABLE"


def test_prediction_must_be_a_participant(client, db, admin_token):
    tid, m = _scheduled(client, db, admin_token)
    ptoken = _predictor_token(client, db)
    other = make_approved_player(db, "outsider-team@example.com", "X")  # a profile id, not a team
    resp = client.post(
        f"/api/v1/matches/{m['id']}/predict",
        json={"winner_team_id": other}, headers=_auth(ptoken),
    )
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "INVALID_PREDICTION"


def test_wrong_prediction_scores_zero(client, db, admin_token):
    tid, m = _scheduled(client, db, admin_token)
    ptoken = _predictor_token(client, db)
    client.post(
        f"/api/v1/matches/{m['id']}/predict",
        json={"winner_team_id": m["team_b_id"]}, headers=_auth(ptoken),
    )
    client.post(
        f"/api/v1/matches/{m['id']}/complete",
        json={"team_a_score": 11, "team_b_score": 5, "expected_version": m["version"]},
        headers=_auth(admin_token),
    )
    board = client.get(f"/api/v1/tournaments/{tid}/predictions/leaderboard").json()
    assert board[0]["points"] == 0 and board[0]["correct"] == 0 and board[0]["total"] == 1
