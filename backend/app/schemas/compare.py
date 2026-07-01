import uuid

from pydantic import BaseModel, Field

from app.schemas.player import PlayerBreakdownOut
from app.schemas.skill import SkillItem


class TeamCompareRequest(BaseModel):
    team_a: list[uuid.UUID] = Field(min_length=1, max_length=2)
    team_b: list[uuid.UUID] = Field(min_length=1, max_length=2)


class MemberBreakdown(BaseModel):
    player_id: uuid.UUID
    name: str
    breakdown: PlayerBreakdownOut


class PairStats(BaseModel):
    matches_played: int
    wins: int
    losses: int
    win_pct: float
    points_for: int
    points_against: int


class TeamCompareSide(BaseModel):
    player_ids: list[uuid.UUID]
    player_names: list[str]
    avg_rating: int
    avg_peak: int
    stats: PairStats
    recent_form: list[str]
    skills: list[SkillItem]
    players: list[MemberBreakdown]


class TeamHeadToHead(BaseModel):
    meetings: int
    a_wins: int
    b_wins: int


class TeamCompareOut(BaseModel):
    team_a: TeamCompareSide
    team_b: TeamCompareSide
    head_to_head: TeamHeadToHead
