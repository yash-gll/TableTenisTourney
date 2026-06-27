import uuid

from pydantic import BaseModel

from app.schemas.match import MatchOut


class PlacementOut(BaseModel):
    place: int
    team_id: uuid.UUID
    team_name: str


class BracketOut(BaseModel):
    matches: list[MatchOut]
    placements: list[PlacementOut]
