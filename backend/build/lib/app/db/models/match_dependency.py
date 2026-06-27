import uuid

from sqlalchemy import Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin
from app.db.models.enums import DependencyOutcome, DependencySlot


class MatchDependency(UUIDMixin, Base):
    """Defines that a target match slot is filled by the winner/loser of a source
    match — used for QF3 and the Final, whose teams are unknown at generation."""

    __tablename__ = "match_dependencies"

    target_match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_slot: Mapped[DependencySlot] = mapped_column(
        Enum(DependencySlot, name="dependency_slot"), nullable=False
    )
    source_match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_outcome: Mapped[DependencyOutcome] = mapped_column(
        Enum(DependencyOutcome, name="dependency_outcome"), nullable=False
    )
