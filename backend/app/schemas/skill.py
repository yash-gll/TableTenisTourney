import uuid

from pydantic import BaseModel, Field


class SkillItem(BaseModel):
    key: str
    label: str
    value: int | None


class PlayerSkillsOut(BaseModel):
    player_id: uuid.UUID
    display_name: str
    skills: list[SkillItem]


class SkillsUpdate(BaseModel):
    # Partial map of {skill_key: 0-100}; validated against the allowed set.
    ratings: dict[str, int] = Field(default_factory=dict)
