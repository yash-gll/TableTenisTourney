import os
from collections.abc import Generator
from datetime import datetime, timezone

# Default to in-memory SQLite so the suite needs no external services.
# Set TEST_DATABASE_URL to a Postgres DSN to run against real Postgres.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
# The app builds its engine from DATABASE_URL at import time; align them so the
# Postgres driver is never imported during the SQLite test run.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base
import app.db.models  # noqa: F401  (register tables)
from app.db.models.enums import AccountStatus, ApprovalStatus, UserRole
from app.db.models.player_profile import PlayerProfile
from app.db.models.user import User
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        TEST_DATABASE_URL,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(TEST_DATABASE_URL, future=True)

TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def _fresh_schema() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# -- helpers -----------------------------------------------------------------


@pytest.fixture()
def make_admin(db: Session):
    def _make(email: str = "admin@example.com", password: str = "adminpass1") -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            account_status=AccountStatus.ACTIVE,
            email_verified_at=datetime.now(tz=timezone.utc),
        )
        db.add(user)
        db.flush()
        db.add(
            PlayerProfile(
                user_id=user.id,
                display_name="Admin",
                approval_status=ApprovalStatus.APPROVED,
            )
        )
        db.commit()
        return user

    return _make


@pytest.fixture()
def admin_token(client: TestClient, make_admin) -> str:
    make_admin()
    resp = client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "adminpass1"}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def register_player(
    client: TestClient,
    email: str = "player@example.com",
    password: str = "playerpass1",
    display_name: str = "Player One",
) -> None:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert resp.status_code == 201, resp.text


def verify_user_directly(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email.lower()).one()
    user.email_verified_at = datetime.now(tz=timezone.utc)
    db.commit()


def make_approved_player(db: Session, email: str, name: str) -> str:
    """Insert a verified, APPROVED player and return its player_profile id (str)."""
    from app.db.models.player_profile import PlayerProfile

    user = User(
        email=email.lower(),
        password_hash=hash_password("playerpass1"),
        role=UserRole.PLAYER,
        account_status=AccountStatus.ACTIVE,
        email_verified_at=datetime.now(tz=timezone.utc),
    )
    db.add(user)
    db.flush()
    profile = PlayerProfile(
        user_id=user.id,
        display_name=name,
        approval_status=ApprovalStatus.APPROVED,
    )
    db.add(profile)
    db.commit()
    return str(profile.id)


def create_tournament(client: TestClient, admin_token: str, name: str = "Summer Cup") -> dict:
    resp = client.post(
        "/api/v1/tournaments",
        json={"name": name},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def setup_closed_tournament(client: TestClient, db: Session, admin_token: str, n_teams: int) -> dict:
    """Create a tournament with `n_teams` complete teams (2 approved players each)
    and move it to REGISTRATION_CLOSED. Returns {tournament, team_ids}."""
    hdr = {"Authorization": f"Bearer {admin_token}"}
    t = create_tournament(client, admin_token, name=f"Cup-{n_teams}")
    tid = t["id"]
    team_ids = []
    for i in range(n_teams):
        team_id = client.post(
            f"/api/v1/tournaments/{tid}/teams", json={"name": f"Team {i + 1}"}, headers=hdr
        ).json()["id"]
        for j in range(2):
            pid = make_approved_player(db, f"t{n_teams}_{i}_{j}@example.com", f"P{i}{j}")
            client.post(
                f"/api/v1/tournaments/{tid}/teams/{team_id}/members",
                json={"player_id": pid},
                headers=hdr,
            )
        team_ids.append(team_id)
    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_OPEN"}, headers=hdr)
    client.post(f"/api/v1/tournaments/{tid}/transition", json={"target": "REGISTRATION_CLOSED"}, headers=hdr)
    return {"tournament_id": tid, "team_ids": team_ids}
