import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import MatchStage, MatchStatus


class MatchOut(BaseModel):
    id: uuid.UUID
    tournament_id: uuid.UUID
    stage: MatchStage
    round_number: int | None
    display_order: int | None
    court_name: str | None
    team_a_id: uuid.UUID | None
    team_b_id: uuid.UUID | None
    team_a_name: str | None
    team_b_name: str | None
    team_a_score: int | None
    team_b_score: int | None
    winner_team_id: uuid.UUID | None
    loser_team_id: uuid.UUID | None
    status: MatchStatus
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    version: int


class LiveMatchOut(BaseModel):
    """A spectatable in-progress match, with the running score already on the row."""

    id: uuid.UUID
    tournament_id: uuid.UUID
    is_exhibition: bool
    context_name: str
    team_a_name: str | None
    team_b_name: str | None
    team_a_score: int | None
    team_b_score: int | None
    status: MatchStatus
    target_points: int


class CompleteRequest(BaseModel):
    team_a_score: int = Field(ge=0)
    team_b_score: int = Field(ge=0)
    expected_version: int = Field(ge=1)


class CorrectRequest(BaseModel):
    team_a_score: int = Field(ge=0)
    team_b_score: int = Field(ge=0)
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=2000)
    reset_dependents: bool = False


class ScheduleGenerateResponse(BaseModel):
    match_count: int
    rounds: int
