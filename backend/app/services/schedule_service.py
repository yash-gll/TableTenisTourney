import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import (
    ApprovalStatus,
    MatchStage,
    MatchStatus,
    TournamentStatus,
)
from app.db.models.match import Match
from app.db.models.team import Team
from app.db.models.tournament import Tournament
from app.db.models.user import User
from app.domain import round_robin
from app.services.audit_service import AuditService

MIN_TEAMS = 2


def pair_key(a: uuid.UUID, b: uuid.UUID) -> str:
    return "|".join(sorted([str(a), str(b)]))


class ScheduleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def generate(self, *, tournament_id: uuid.UUID, actor: User, meta: dict) -> tuple[int, int]:
        tournament = self.db.get(Tournament, tournament_id)
        if tournament is None:
            raise errors.tournament_not_found()

        # Idempotency: refuse if matches already exist (checked before status so a
        # repeat call after scheduling reports the right error).
        existing = self.db.execute(
            select(func.count()).select_from(Match).where(Match.tournament_id == tournament_id)
        ).scalar_one()
        if existing:
            raise errors.schedule_already_generated()

        if tournament.status != TournamentStatus.REGISTRATION_CLOSED:
            raise errors.match_not_editable(
                "Close registration before generating the schedule."
            )

        teams = list(
            self.db.execute(
                select(Team).where(Team.tournament_id == tournament_id).order_by(Team.created_at)
            ).scalars()
        )
        if len(teams) < MIN_TEAMS:
            raise errors.not_enough_teams(MIN_TEAMS)

        # Every team must have exactly two approved players.
        for team in teams:
            members = team.members
            if len(members) != 2 or any(
                m.player.approval_status != ApprovalStatus.APPROVED for m in members
            ):
                raise errors.team_requires_two_players()

        team_ids = [str(t.id) for t in teams]
        rounds = round_robin.generate_round_robin(team_ids)
        round_robin.validate_schedule(team_ids, rounds)

        display = 0
        for round_index, rnd in enumerate(rounds, start=1):
            for a, b in rnd:
                a_id, b_id = uuid.UUID(a), uuid.UUID(b)
                display += 1
                self.db.add(
                    Match(
                        tournament_id=tournament_id,
                        stage=MatchStage.GROUP,
                        round_number=round_index,
                        display_order=display,
                        team_a_id=a_id,
                        team_b_id=b_id,
                        status=MatchStatus.SCHEDULED,
                        pair_key=pair_key(a_id, b_id),
                        created_by=actor.id,
                    )
                )

        tournament.status = TournamentStatus.SCHEDULED
        self.audit.record(
            actor_user_id=actor.id,
            action="schedule.generate",
            entity_type="tournament",
            entity_id=str(tournament_id),
            after_data={"match_count": display, "rounds": len(rounds)},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        return display, len(rounds)

    def list_matches(self, tournament_id: uuid.UUID) -> list[Match]:
        return list(
            self.db.execute(
                select(Match)
                .where(Match.tournament_id == tournament_id)
                .order_by(Match.stage, Match.round_number, Match.display_order)
            ).scalars()
        )
