import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models.enums import ApprovalStatus


class AdminPlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    email: EmailStr
    approval_status: ApprovalStatus
    approval_reason: str | None
    email_verified: bool
    created_at: datetime


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class SuspendRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)
