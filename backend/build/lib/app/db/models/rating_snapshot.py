import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin
from app.db.models.enums import SnapshotType


class RatingSnapshot(UUIDMixin, Base):
    __tablename__ = "rating_snapshots"

    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_type: Mapped[SnapshotType] = mapped_column(
        Enum(SnapshotType, name="snapshot_type"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
