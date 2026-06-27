from app.core.config import settings
from app.core.ratelimit import reset_rate_limits


def test_request_id_header_present(client):
    resp = client.get("/api/v1/health")
    assert resp.headers.get("X-Request-ID")


def test_error_envelope_has_request_id(client):
    resp = client.get("/api/v1/admin/players")  # 401, unauthenticated
    assert resp.status_code == 401
    assert resp.json()["error"]["request_id"]


def test_rate_limit_blocks_burst(client):
    reset_rate_limits()
    settings.rate_limit_enabled = True
    try:
        codes = []
        for _ in range(12):
            r = client.post(
                "/api/v1/auth/login", json={"email": "x@example.com", "password": "nope"}
            )
            codes.append(r.status_code)
        # login limit is 10/min; the 11th+ request is rejected.
        assert 429 in codes
        assert codes[:10] == [401] * 10
        assert codes[10] == 429
        assert client.post(
            "/api/v1/auth/login", json={"email": "x@example.com", "password": "nope"}
        ).json()["error"]["code"] == "RATE_LIMITED"
    finally:
        settings.rate_limit_enabled = False
        reset_rate_limits()
