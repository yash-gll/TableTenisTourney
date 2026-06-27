import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin

_JSONType = JSON().with_variant(JSONB(), "postgresql")


class TournamentResult(UUIDMixin, Base):
    __tablename__ = "tournament_results"

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("tournaments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    champion_team_id: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    runner_up_team_id: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    third_place_team_id: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    fourth_place_team_id: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    final_group_leaderboard: Mapped[dict | None] = mapped_column(_JSONType)
    final_bracket: Mapped[dict | None] = mapped_column(_JSONType)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalized_by: Mapped[uuid.UUID | None] = mapped_column(Uuid())
