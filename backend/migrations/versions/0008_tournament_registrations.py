"""tournament_registrations

Revision ID: 0008_tournament_registrations
Revises: 0007_skill_ratings
Create Date: 2026-06-27

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_tournament_registrations"
down_revision: str | None = "0007_skill_ratings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    registration_status = postgresql.ENUM(
        "REQUESTED", "ACCEPTED", "WAITLISTED", "DECLINED", "WITHDRAWN", name="registration_status"
    )
    op.create_table(
        "tournament_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tournament_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "player_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("status", registration_status, nullable=False, server_default="REQUESTED"),
        sa.Column(
            "preferred_partner_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tournament_id", "player_id", name="uq_registration_tournament_player"),
    )
    op.create_index("ix_tournament_registrations_tournament_id", "tournament_registrations", ["tournament_id"])
    op.create_index("ix_tournament_registrations_player_id", "tournament_registrations", ["player_id"])


def downgrade() -> None:
    op.drop_table("tournament_registrations")
    op.execute("DROP TYPE IF EXISTS registration_status")
