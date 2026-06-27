import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin
from app.db.models.enums import RegistrationStatus


class TournamentRegistration(UUIDMixin, Base):
    """A player's request to join a tournament (admin still forms the teams)."""

    __tablename__ = "tournament_registrations"
    __table_args__ = (
        UniqueConstraint("tournament_id", "player_id", name="uq_registration_tournament_player"),
    )

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status"),
        default=RegistrationStatus.REQUESTED,
        nullable=False,
    )
    preferred_partner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("player_profiles.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
