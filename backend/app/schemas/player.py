import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models.enums import AccountStatus, ApprovalStatus, UserRole


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)


class PlayerProfileOut(BaseModel):
    """Player's own / admin view — includes email and account info."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    email: EmailStr
    role: UserRole
    account_status: AccountStatus
    approval_status: ApprovalStatus
    approval_reason: str | None
    current_rating: int
    highest_rating: int
    bio: str | None
    email_verified: bool
    created_at: datetime


class MeResponse(BaseModel):
    """Result of GET /auth/me."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: EmailStr
    role: UserRole
    account_status: AccountStatus
    email_verified: bool
    approval_status: ApprovalStatus
    display_name: str
