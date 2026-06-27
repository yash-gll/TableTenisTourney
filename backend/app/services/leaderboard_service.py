import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import MatchStage, MatchStatus, TournamentStatus
from app.db.models.match import Match
from app.db.models.team import Team
from app.db.models.tournament import Tournament
from app.db.models.user import User
from app.domain import leaderboard as lb
from app.services.audit_service import AuditService

GROUP_DONE_STATES = {
    TournamentStatus.GROUP_COMPLETE,
    TournamentStatus.QUALIFIERS_IN_PROGRESS,
    TournamentStatus.COMPLETED,
    TournamentStatus.FINALIZED,
    TournamentStatus.ARCHIVED,
}


class LeaderboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def _tournament(self, tournament_id: uuid.UUID) -> Tournament:
        t = self.db.get(Tournament, tournament_id)
        if t is None:
            raise errors.tournament_not_found()
        return t

    def _teams(self, tournament_id: uuid.UUID) -> list[Team]:
        return list(
            self.db.execute(
                select(Team).where(Team.tournament_id == tournament_id).order_by(Team.created_at)
            ).scalars()
        )

    def compute(
        self, tournament_id: uuid.UUID
    ) -> tuple[lb.LeaderboardResult, dict[str, str], bool]:
        tournament = self._tournament(tournament_id)
        teams = self._teams(tournament_id)
        names = {str(t.id): t.name for t in teams}
        seeds = [lb.TeamSeed(team_id=str(t.id), seed=t.initial_seed) for t in teams]

        completed = self.db.execute(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == MatchStage.GROUP,
                Match.status == MatchStatus.COMPLETED,
            )
        ).scalars()
        results: list[lb.MatchResult] = []
        for m in completed:
            if (
                m.team_a_id is None
                or m.team_b_id is None
                or m.team_a_score is None
                or m.team_b_score is None
            ):
                continue
            results.append(
                lb.MatchResult(
                    team_a=str(m.team_a_id),
                    team_b=str(m.team_b_id),
                    a_score=m.team_a_score,
                    b_score=m.team_b_score,
                )
            )

        group_complete = tournament.status in GROUP_DONE_STATES
        manual = {str(k): int(v) for k, v in (tournament.manual_rankings or {}).items()}

        result = lb.compute_standings(
            seeds,
            results,
            win_table_points=tournament.win_table_points,
            loss_table_points=tournament.loss_table_points,
            manual_rankings=manual,
            group_complete=group_complete,
        )
        return result, names, group_complete

    def resolve_tie(
        self, *, tournament_id: uuid.UUID, ordering: list[uuid.UUID], reason: str, actor: User,
        meta: dict,
    ) -> None:
        tournament = self._tournament(tournament_id)
        # Store as {team_id: position} merged into existing manual rankings.
        manual = dict(tournament.manual_rankings or {})
        for position, team_id in enumerate(ordering):
            manual[str(team_id)] = position
        tournament.manual_rankings = manual
        self.audit.record(
            actor_user_id=actor.id,
            action="leaderboard.resolve_tie",
            entity_type="tournament",
            entity_id=str(tournament_id),
            after_data={"ordering": [str(t) for t in ordering]},
            reason=reason,
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
