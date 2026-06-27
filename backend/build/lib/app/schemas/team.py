import uuid

from pydantic import BaseModel, Field


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    initial_seed: int | None = Field(default=None, ge=1)
    logo_url: str | None = Field(default=None, max_length=500)


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    initial_seed: int | None = Field(default=None, ge=1)
    logo_url: str | None = Field(default=None, max_length=500)


class AddMemberRequest(BaseModel):
    player_id: uuid.UUID


class TeamMemberOut(BaseModel):
    player_id: uuid.UUID
    display_name: str
    current_rating: int
    member_order: int


class TeamOut(BaseModel):
    id: uuid.UUID
    tournament_id: uuid.UUID
    name: str
    logo_url: str | None
    initial_seed: int | None
    members: list[TeamMemberOut]
    average_rating: float | None
    is_complete: bool
