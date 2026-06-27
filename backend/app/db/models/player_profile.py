import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.models.enums import ApprovalStatus

if TYPE_CHECKING:
    from app.db.models.user import User

STARTING_RATING = 1000


class PlayerProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "player_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"),
        default=ApprovalStatus.PENDING,
        nullable=False,
    )
    approval_reason: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    current_rating: Mapped[int] = mapped_column(Integer, default=STARTING_RATING, nullable=False)
    highest_rating: Mapped[int] = mapped_column(Integer, default=STARTING_RATING, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(
        back_populates="profile", foreign_keys=[user_id]
    )
