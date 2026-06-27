"""matches table + match enums + tournaments.manual_rankings

Revision ID: 0003_matches
Revises: 0002_tournaments_teams
Create Date: 2026-06-26

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_matches"
down_revision: str | None = "0002_tournaments_teams"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    match_status = postgresql.ENUM(
        "WAITING_FOR_TEAMS",
        "SCHEDULED",
        "IN_PROGRESS",
        "COMPLETED",
        "CANCELLED",
        "VOID",
        name="match_status",
    )
    match_stage = postgresql.ENUM(
        "GROUP", "QF1", "QF2", "QF3", "FINAL", "TIEBREAKER", name="match_stage"
    )

    op.add_column("tournaments", sa.Column("manual_rankings", postgresql.JSONB(), nullable=True))

    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tournament_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage", match_stage, nullable=False, server_default="GROUP"),
        sa.Column("round_number", sa.Integer(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("court_name", sa.String(length=80), nullable=True),
        sa.Column(
            "team_a_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "team_b_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("team_a_score", sa.Integer(), nullable=True),
        sa.Column("team_b_score", sa.Integer(), nullable=True),
        sa.Column(
            "winner_team_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "loser_team_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("status", match_status, nullable=False, server_default="SCHEDULED"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pair_key", sa.String(length=80), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "team_a_id IS NULL OR team_b_id IS NULL OR team_a_id <> team_b_id",
            name="ck_match_distinct_teams",
        ),
        sa.CheckConstraint("team_a_score IS NULL OR team_a_score >= 0", name="ck_match_a_score_nonneg"),
        sa.CheckConstraint("team_b_score IS NULL OR team_b_score >= 0", name="ck_match_b_score_nonneg"),
        sa.UniqueConstraint("tournament_id", "stage", "pair_key", name="uq_match_pair"),
    )
    op.create_index("ix_matches_tournament_id", "matches", ["tournament_id"])


def downgrade() -> None:
    op.drop_table("matches")
    op.drop_column("tournaments", "manual_rankings")
    for enum_name in ("match_stage", "match_status"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
