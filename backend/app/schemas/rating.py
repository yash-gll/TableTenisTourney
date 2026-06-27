import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RatingConfigOut(BaseModel):
    starting_rating: int
    rating_floor: int
    group_k: int
    qf1_k: int
    qf2_k: int
    qf3_k: int
    final_k: int
    champion_bonus: int
    runner_up_bonus: int
    third_place_bonus: int


class RatingConfigUpdate(BaseModel):
    group_k: int | None = Field(default=None, ge=1, le=100)
    qf1_k: int | None = Field(default=None, ge=1, le=100)
    qf2_k: int | None = Field(default=None, ge=1, le=100)
    qf3_k: int | None = Field(default=None, ge=1, le=100)
    final_k: int | None = Field(default=None, ge=1, le=100)
    champion_bonus: int | None = Field(default=None, ge=0, le=500)
    runner_up_bonus: int | None = Field(default=None, ge=0, le=500)
    third_place_bonus: int | None = Field(default=None, ge=0, le=500)
    starting_rating: int | None = Field(default=None, ge=100, le=3000)
    rating_floor: int | None = Field(default=None, ge=0, le=1000)


class RatingEventOut(BaseModel):
    id: uuid.UUID
    tournament_id: uuid.UUID | None
    match_id: uuid.UUID | None
    event_type: str
    rating_before: int
    delta: int
    rating_after: int
    reason: str | None
    created_at: datetime


class RatingAdjustment(BaseModel):
    delta: int = Field(ge=-1000, le=1000)
    reason: str = Field(min_length=1, max_length=2000)


class RecalculateRequest(BaseModel):
    tournament_id: uuid.UUID
