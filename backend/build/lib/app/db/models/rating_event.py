import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin
from app.db.models.enums import RatingEventType

_JSONType = JSON().with_variant(JSONB(), "postgresql")


class RatingEvent(UUIDMixin, Base):
    """Append-only ledger: a rating never changes without an event."""

    __tablename__ = "rating_events"

    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("tournaments.id", ondelete="CASCADE"), index=True
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("matches.id", ondelete="SET NULL")
    )
    event_type: Mapped[RatingEventType] = mapped_column(
        Enum(RatingEventType, name="rating_event_type"), nullable=False
    )
    rating_before: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_after: Mapped[int] = mapped_column(Integer, nullable=False)
    calculation_data: Mapped[dict | None] = mapped_column(_JSONType)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_superseded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
