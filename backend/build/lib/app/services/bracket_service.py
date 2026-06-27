import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import (
    AuditSeverity,
    DependencyOutcome,
    DependencySlot,
    MatchStage,
    MatchStatus,
    TournamentStatus,
)
from app.db.models.match import Match
from app.db.models.match_dependency import MatchDependency
from app.db.models.tournament import Tournament
from app.db.models.user import User
from app.domain import bracket as bd
from app.domain import leaderboard as lb
from app.services.audit_service import AuditService
from app.services.leaderboard_service import LeaderboardService

MIN_BRACKET_TEAMS = 4
STARTED_STATES = {MatchStatus.IN_PROGRESS, MatchStatus.COMPLETED}


class BracketService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    # -- queries -----------------------------------------------------------

    def _bracket_matches(self, tournament_id: uuid.UUID) -> list[Match]:
        return list(
            self.db.execute(
                select(Match)
                .where(
                    Match.tournament_id == tournament_id,
                    Match.stage.in_(bd.BRACKET_STAGES),
                )
                .order_by(Match.display_order)
            ).scalars()
        )

    def _stage_map(self, tournament_id: uuid.UUID) -> dict[MatchStage, Match]:
        return {m.stage: m for m in self._bracket_matches(tournament_id)}

    def _dependents_of(self, match: Match) -> list[Match]:
        deps = self.db.execute(
            select(MatchDependency).where(MatchDependency.source_match_id == match.id)
        ).scalars()
        targets = []
        for d in deps:
            t = self.db.get(Match, d.target_match_id)
            if t is not None:
                targets.append(t)
        return targets

    # -- generation --------------------------------------------------------

    def generate(self, *, tournament_id: uuid.UUID, actor: User, meta: dict) -> list[Match]:
        tournament = self.db.get(Tournament, tournament_id)
        if tournament is None:
            raise errors.tournament_not_found()
        if tournament.status != TournamentStatus.GROUP_COMPLETE:
            raise errors.group_stage_incomplete()

        if self._bracket_matches(tournament_id):
            raise errors.bracket_already_generated()

        result, _, group_complete = LeaderboardService(self.db).compute(tournament_id)
        if not group_complete:
            raise errors.group_stage_incomplete()
        if len(result.standings) < MIN_BRACKET_TEAMS:
            raise errors.not_enough_teams(MIN_BRACKET_TEAMS)
        if lb.has_unresolved_top_tie(result):
            raise errors.qualification_tie_unresolved()

        ranks = [uuid.UUID(result.standings[i].team_id) for i in range(4)]
        self._create_bracket(tournament_id, ranks, actor)

        tournament.status = TournamentStatus.QUALIFIERS_IN_PROGRESS
        self.audit.record(
            actor_user_id=actor.id, action="bracket.generate", entity_type="tournament",
            entity_id=str(tournament_id),
            after_data={"ranks": [str(r) for r in ranks]},
            ip_address=meta.get("ip_address"), user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        return self._bracket_matches(tournament_id)

    def _create_bracket(self, tournament_id: uuid.UUID, ranks: list[uuid.UUID], actor: User) -> None:
        r1, r2, r3, r4 = ranks
        stage_matches: dict[MatchStage, Match] = {}
        seeds = {
            MatchStage.QF1: (r1, r2, MatchStatus.SCHEDULED, 1),
            MatchStage.QF2: (r3, r4, MatchStatus.SCHEDULED, 2),
            MatchStage.QF3: (None, None, MatchStatus.WAITING_FOR_TEAMS, 3),
            MatchStage.FINAL: (None, None, MatchStatus.WAITING_FOR_TEAMS, 4),
        }
        for stage, (a, b, st, order) in seeds.items():
            m = Match(
                tournament_id=tournament_id, stage=stage, team_a_id=a, team_b_id=b,
                status=st, display_order=order, created_by=actor.id,
            )
            self.db.add(m)
            stage_matches[stage] = m
        self.db.flush()

        for target_stage, slot, source_stage, outcome in bd.DEPENDENCIES:
            self.db.add(
                MatchDependency(
                    target_match_id=stage_matches[target_stage].id,
                    target_slot=slot,
                    source_match_id=stage_matches[source_stage].id,
                    source_outcome=outcome,
                )
            )

    def rebuild(self, *, tournament_id: uuid.UUID, actor: User, meta: dict) -> list[Match]:
        tournament = self.db.get(Tournament, tournament_id)
        if tournament is None:
            raise errors.tournament_not_found()
        for m in self._bracket_matches(tournament_id):
            self.db.delete(m)  # cascades dependencies via FK
        self.db.flush()
        tournament.status = TournamentStatus.GROUP_COMPLETE
        self.audit.record(
            actor_user_id=actor.id, action="bracket.rebuild", entity_type="tournament",
            entity_id=str(tournament_id), severity=AuditSeverity.CRITICAL,
            ip_address=meta.get("ip_address"), user_agent=meta.get("user_agent"),
        )
        return self.generate(tournament_id=tournament_id, actor=actor, meta=meta)

    # -- propagation -------------------------------------------------------

    def propagate_from(self, match: Match) -> None:
        deps = self.db.execute(
            select(MatchDependency).where(MatchDependency.source_match_id == match.id)
        ).scalars()
        for d in deps:
            target = self.db.get(Match, d.target_match_id)
            if target is None:
                continue
            team = (
                match.winner_team_id
                if d.source_outcome == DependencyOutcome.WINNER
                else match.loser_team_id
            )
            if d.target_slot == DependencySlot.TEAM_A:
                target.team_a_id = team
            else:
                target.team_b_id = team
            if (
                target.team_a_id is not None
                and target.team_b_id is not None
                and target.status == MatchStatus.WAITING_FOR_TEAMS
            ):
                target.status = MatchStatus.SCHEDULED
        self.db.flush()

    def has_started_dependents(self, match: Match) -> bool:
        return any(t.status in STARTED_STATES for t in self._dependents_of(match))

    def reset_cascade(self, match: Match, actor: User, meta: dict) -> None:
        """Reset every match that depends on `match` (and their downstream),
        clearing dependency-fed slots and results. Critical, audited."""
        for target in self._dependents_of(match):
            self.reset_cascade(target, actor, meta)
            deps_into = self.db.execute(
                select(MatchDependency).where(MatchDependency.target_match_id == target.id)
            ).scalars()
            for d in deps_into:
                if d.target_slot == DependencySlot.TEAM_A:
                    target.team_a_id = None
                else:
                    target.team_b_id = None
            target.team_a_score = None
            target.team_b_score = None
            target.winner_team_id = None
            target.loser_team_id = None
            target.started_at = None
            target.completed_at = None
            target.status = MatchStatus.WAITING_FOR_TEAMS
            target.version += 1
            self.audit.record(
                actor_user_id=actor.id, action="bracket.reset_dependent", entity_type="match",
                entity_id=str(target.id), severity=AuditSeverity.CRITICAL,
                ip_address=meta.get("ip_address"), user_agent=meta.get("user_agent"),
            )
        self.db.flush()

    # -- placements --------------------------------------------------------

    def placements(self, tournament_id: uuid.UUID) -> dict[str, int]:
        stages = self._stage_map(tournament_id)

        def done(stage: MatchStage) -> Match | None:
            m = stages.get(stage)
            return m if m and m.status == MatchStatus.COMPLETED else None

        final = done(MatchStage.FINAL)
        qf3 = done(MatchStage.QF3)
        qf2 = done(MatchStage.QF2)
        return bd.placement_map(
            final_winner=str(final.winner_team_id) if final else None,
            final_loser=str(final.loser_team_id) if final else None,
            qf3_loser=str(qf3.loser_team_id) if qf3 else None,
            qf2_loser=str(qf2.loser_team_id) if qf2 else None,
        )

    def get_bracket(self, tournament_id: uuid.UUID) -> tuple[list[Match], dict[str, int]]:
        return self._bracket_matches(tournament_id), self.placements(tournament_id)
