import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import TournamentStatus, TournamentVisibility


class ScoringConfig(BaseModel):
    target_points: int = Field(default=11, ge=1, le=99)
    win_by_two: bool = False
    maximum_points: int | None = Field(default=None, ge=1, le=99)
    win_table_points: int = Field(default=2, ge=0, le=10)
    loss_table_points: int = Field(default=0, ge=0, le=10)


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    location: str | None = Field(default=None, max_length=200)
    start_at: datetime | None = None
    end_at: datetime | None = None
    visibility: TournamentVisibility = TournamentVisibility.PUBLIC
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)


class TournamentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    location: str | None = Field(default=None, max_length=200)
    start_at: datetime | None = None
    end_at: datetime | None = None
    visibility: TournamentVisibility | None = None
    scoring: ScoringConfig | None = None


class TransitionRequest(BaseModel):
    target: TournamentStatus
    reason: str | None = Field(default=None, max_length=2000)


class TournamentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    location: str | None
    start_at: datetime | None
    end_at: datetime | None
    status: TournamentStatus
    visibility: TournamentVisibility
    target_points: int
    win_by_two: bool
    maximum_points: int | None
    win_table_points: int
    loss_table_points: int
    version: int
    team_count: int = 0
    is_editable: bool = False
    created_at: datetime
