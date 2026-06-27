import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin


class MatchPrediction(UUIDMixin, Base):
    """A player's pick for who wins a match (engagement / pick'em)."""

    __tablename__ = "match_predictions"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_prediction_match_player"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    predicted_winner_team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
