import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import RegistrationStatus


class RegistrationCreate(BaseModel):
    preferred_partner_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=500)


class RegistrationOut(BaseModel):
    player_id: uuid.UUID
    display_name: str
    status: RegistrationStatus
    preferred_partner_id: uuid.UUID | None
    note: str | None
    created_at: datetime


class MyRegistrationOut(BaseModel):
    status: RegistrationStatus | None  # null = not registered
