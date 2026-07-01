import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.models.enums import MatchStage, MatchStatus

_JSONType = JSON().with_variant(JSONB(), "postgresql")

if TYPE_CHECKING:
    from app.db.models.team import Team


class Match(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint(
            "team_a_id IS NULL OR team_b_id IS NULL OR team_a_id <> team_b_id",
            name="ck_match_distinct_teams",
        ),
        CheckConstraint(
            "team_a_score IS NULL OR team_a_score >= 0", name="ck_match_a_score_nonneg"
        ),
        CheckConstraint(
            "team_b_score IS NULL OR team_b_score >= 0", name="ck_match_b_score_nonneg"
        ),
        # One match per unordered team pair per tournament+stage (group dedupe).
        UniqueConstraint("tournament_id", "stage", "pair_key", name="uq_match_pair"),
    )

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[MatchStage] = mapped_column(
        Enum(MatchStage, name="match_stage"), nullable=False, default=MatchStage.GROUP
    )
    round_number: Mapped[int | None] = mapped_column(Integer)
    display_order: Mapped[int | None] = mapped_column(Integer)
    court_name: Mapped[str | None] = mapped_column(String(80))

    team_a_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("teams.id", ondelete="SET NULL")
    )
    team_b_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("teams.id", ondelete="SET NULL")
    )
    team_a_score: Mapped[int | None] = mapped_column(Integer)
    team_b_score: Mapped[int | None] = mapped_column(Integer)
    winner_team_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("teams.id", ondelete="SET NULL")
    )
    loser_team_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("teams.id", ondelete="SET NULL")
    )

    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="match_status"), nullable=False, default=MatchStatus.SCHEDULED
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Sorted "a|b" of the two team ids; stable key for the unique group pairing.
    pair_key: Mapped[str | None] = mapped_column(String(80))
    # Diagonal serve pairing {player_id: opponent_id} — drives the forced-error
    # "who forced it?" auto-suggestion. Null until set (or trivial for singles).
    serve_pairing: Mapped[dict | None] = mapped_column(_JSONType)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    admin_note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL")
    )

    team_a: Mapped["Team | None"] = relationship(foreign_keys=[team_a_id])
    team_b: Mapped["Team | None"] = relationship(foreign_keys=[team_b_id])
