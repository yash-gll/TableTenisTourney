import uuid

from pydantic import BaseModel, Field

from app.schemas.match import MatchOut


class ExhibitionOut(MatchOut):
    team_a_players: list[str] = []
    team_b_players: list[str] = []


class ExhibitionSide(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    player_ids: list[uuid.UUID] = Field(min_length=1, max_length=2)


class ExhibitionCreate(BaseModel):
    label: str | None = Field(default=None, max_length=160)
    team_a: ExhibitionSide
    team_b: ExhibitionSide
    target_points: int = Field(default=11, ge=1, le=99)
    win_by_two: bool = False
