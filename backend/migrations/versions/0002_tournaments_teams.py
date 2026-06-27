"""tournaments, teams, team_members

Revision ID: 0002_tournaments_teams
Revises: 0001_initial
Create Date: 2026-06-26

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_tournaments_teams"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tournament_status = postgresql.ENUM(
        "DRAFT",
        "REGISTRATION_OPEN",
        "REGISTRATION_CLOSED",
        "SCHEDULED",
        "GROUP_IN_PROGRESS",
        "GROUP_COMPLETE",
        "QUALIFIERS_IN_PROGRESS",
        "COMPLETED",
        "FINALIZED",
        "PAUSED",
        "CANCELLED",
        "ARCHIVED",
        name="tournament_status",
    )
    tournament_visibility = postgresql.ENUM(
        "PUBLIC", "PRIVATE", "UNLISTED", name="tournament_visibility"
    )

    op.create_table(
        "tournaments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", tournament_status, nullable=False, server_default="DRAFT"),
        sa.Column("visibility", tournament_visibility, nullable=False, server_default="PUBLIC"),
        sa.Column("target_points", sa.Integer(), nullable=False, server_default="11"),
        sa.Column("win_by_two", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("maximum_points", sa.Integer(), nullable=True),
        sa.Column("win_table_points", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("loss_table_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rating_status", sa.String(length=40), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_tournaments_slug", "tournaments", ["slug"], unique=True)

    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tournament_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("initial_seed", sa.Integer(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tournament_id", "name", name="uq_team_tournament_name"),
    )
    op.create_index("ix_teams_tournament_id", "teams", ["tournament_id"])

    op.create_table(
        "team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tournament_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("member_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("team_id", "player_id", name="uq_member_team_player"),
        sa.UniqueConstraint("team_id", "member_order", name="uq_member_team_order"),
        sa.UniqueConstraint("tournament_id", "player_id", name="uq_member_tournament_player"),
    )
    op.create_index("ix_team_members_tournament_id", "team_members", ["tournament_id"])
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"])
    op.create_index("ix_team_members_player_id", "team_members", ["player_id"])


def downgrade() -> None:
    op.drop_table("team_members")
    op.drop_table("teams")
    op.drop_index("ix_tournaments_slug", table_name="tournaments")
    op.drop_table("tournaments")
    for enum_name in ("tournament_visibility", "tournament_status"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
