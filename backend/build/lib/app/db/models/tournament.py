import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.models.enums import TournamentStatus, TournamentVisibility

_JSONType = JSON().with_variant(JSONB(), "postgresql")

if TYPE_CHECKING:
    from app.db.models.team import Team


class Tournament(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tournaments"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[TournamentStatus] = mapped_column(
        Enum(TournamentStatus, name="tournament_status"),
        default=TournamentStatus.DRAFT,
        nullable=False,
    )
    visibility: Mapped[TournamentVisibility] = mapped_column(
        Enum(TournamentVisibility, name="tournament_visibility"),
        default=TournamentVisibility.PUBLIC,
        nullable=False,
    )

    # Scoring configuration (used from Phase 3 onward).
    target_points: Mapped[int] = mapped_column(Integer, default=11, nullable=False)
    win_by_two: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maximum_points: Mapped[int | None] = mapped_column(Integer)
    win_table_points: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    loss_table_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL")
    )
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rating_status: Mapped[str | None] = mapped_column(String(40))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # Admin tie-break override: {team_id: order_int}, applied only within a tied group.
    manual_rankings: Mapped[dict | None] = mapped_column(_JSONType)

    teams: Mapped[list["Team"]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
        order_by="Team.created_at",
    )
