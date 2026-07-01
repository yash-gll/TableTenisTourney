import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models.enums import AccountStatus, ApprovalStatus, UserRole


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)


class PlayerProfileOut(BaseModel):
    """Player's own / admin view — includes email and account info."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    email: EmailStr
    role: UserRole
    account_status: AccountStatus
    approval_status: ApprovalStatus
    approval_reason: str | None
    current_rating: int
    highest_rating: int
    bio: str | None
    skill_ratings: dict[str, int] = {}
    email_verified: bool
    created_at: datetime


class PublicPlayerOut(BaseModel):
    """Directory entry — public-safe (no email)."""

    player_id: uuid.UUID
    display_name: str
    current_rating: int
    highest_rating: int
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    win_pct: float = 0.0
    rallies_played: int = 0
    rallies_won: int = 0
    rallies_lost: int = 0
    rally_win_pct: float = 0.0


class PlayerStatsOut(BaseModel):
    matches_played: int
    wins: int
    losses: int
    win_pct: float
    tournaments_played: int
    tournament_wins: int


class PublicProfileOut(BaseModel):
    player_id: uuid.UUID
    display_name: str
    current_rating: int
    highest_rating: int
    stats: PlayerStatsOut
    recent_form: list[str] = []  # most-recent-first ["W","L",...]


class RivalOut(BaseModel):
    opponent_id: uuid.UUID
    opponent_name: str
    meetings: int
    wins: int
    losses: int


class PlayerRivalsOut(BaseModel):
    player_id: uuid.UUID
    rivals: list[RivalOut]


class SkillCount(BaseModel):
    key: str
    label: str
    count: int


class PlayerBreakdownOut(BaseModel):
    player_id: uuid.UUID
    total_points: int
    wins: int
    faults: int
    forced_faults: int
    unforced_faults: int
    points_forced: int
    win_by_skill: list[SkillCount]
    faults_by_type: list[SkillCount]


class BadgeOut(BaseModel):
    key: str
    label: str
    icon: str
    description: str


class PlayerAchievementsOut(BaseModel):
    player_id: uuid.UUID
    achievements: list[BadgeOut]


class MeResponse(BaseModel):
    """Result of GET /auth/me."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: EmailStr
    role: UserRole
    account_status: AccountStatus
    email_verified: bool
    approval_status: ApprovalStatus
    display_name: str
