import uuid

from pydantic import BaseModel, Field


class StandingOut(BaseModel):
    rank: int
    team_id: uuid.UUID
    team_name: str
    played: int
    wins: int
    losses: int
    table_points: int
    points_for: int
    points_against: int
    point_difference: int
    tie_status: str
    qualification_status: str


class LeaderboardOut(BaseModel):
    group_complete: bool
    standings: list[StandingOut]


class ExplanationOut(BaseModel):
    explanation: list[str]


class ResolveTieRequest(BaseModel):
    # Desired order (highest first) for a set of tied teams.
    ordering: list[uuid.UUID] = Field(min_length=2)
    reason: str = Field(min_length=1, max_length=2000)
