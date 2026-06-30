import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin


class MatchPoint(UUIDMixin, Base):
    """One rally, won by a player using a skill — the raw signal that drives
    play-derived skill ratings. The match score is the count of these per team."""

    __tablename__ = "match_points"

    match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
