import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import AuditSeverity, MatchStage, MatchStatus, TournamentStatus
from app.db.models.match import Match
from app.db.models.tournament import Tournament
from app.db.models.user import User
from app.domain import scoring
from app.services.audit_service import AuditService


def _now() -> datetime:
    return datetime.now(tz=UTC)


class ScoringService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    # -- helpers -----------------------------------------------------------

    def get_match(self, match_id: uuid.UUID) -> Match:
        match = self.db.get(Match, match_id)
        if match is None:
            raise errors.match_not_found()
        return match

    def _tournament(self, match: Match) -> Tournament:
        t = self.db.get(Tournament, match.tournament_id)
        if t is None:
            raise errors.tournament_not_found()
        return t

    def _check_version(self, match: Match, expected: int) -> None:
        if match.version != expected:
            raise errors.match_version_conflict(match.version)

    def _resolve(self, tournament: Tournament, a: int, b: int) -> scoring.WinnerSide:
        rules = scoring.ScoringRules(
            target_points=tournament.target_points,
            win_by_two=tournament.win_by_two,
            maximum_points=tournament.maximum_points,
        )
        try:
            return scoring.resolve_winner(rules, a, b)
        except scoring.InvalidScore as e:
            raise errors.invalid_match_score(
                e.message,
                {"target_points": tournament.target_points, "win_by_two": tournament.win_by_two},
            ) from e

    def _apply_result(self, match: Match, a: int, b: int, side: scoring.WinnerSide) -> None:
        match.team_a_score = a
        match.team_b_score = b
        if side == "A":
            match.winner_team_id, match.loser_team_id = match.team_a_id, match.team_b_id
        else:
            match.winner_team_id, match.loser_team_id = match.team_b_id, match.team_a_id

    # -- transitions -------------------------------------------------------

    def start_match(self, *, match_id: uuid.UUID, actor: User, meta: dict) -> Match:
        match = self.get_match(match_id)
        if match.status != MatchStatus.SCHEDULED:
            raise errors.match_not_editable("Only a scheduled match can be started.")
        if match.team_a_id is None or match.team_b_id is None:
            raise errors.match_not_editable("Both teams must be known before starting.")

        match.status = MatchStatus.IN_PROGRESS
        match.started_at = _now()
        match.version += 1
        match.updated_by = actor.id

        tournament = self._tournament(match)
        if match.stage == MatchStage.GROUP and tournament.status == TournamentStatus.SCHEDULED:
            tournament.status = TournamentStatus.GROUP_IN_PROGRESS

        self.audit.record(
            actor_user_id=actor.id, action="match.start", entity_type="match",
            entity_id=str(match.id), ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(match)
        return match

    def complete_match(
        self, *, match_id: uuid.UUID, a: int, b: int, expected_version: int, actor: User, meta: dict
    ) -> Match:
        match = self.get_match(match_id)
        if match.status not in (MatchStatus.SCHEDULED, MatchStatus.IN_PROGRESS):
            raise errors.match_not_editable("Only a scheduled or in-progress match can be completed.")
        self._check_version(match, expected_version)
        if match.team_a_id is None or match.team_b_id is None:
            raise errors.match_not_editable("Both teams must be known before completing.")

        tournament = self._tournament(match)
        side = self._resolve(tournament, a, b)
        self._apply_result(match, a, b, side)
        match.status = MatchStatus.COMPLETED
        match.completed_at = _now()
        match.version += 1
        match.updated_by = actor.id

        self.audit.record(
            actor_user_id=actor.id, action="match.complete", entity_type="match",
            entity_id=str(match.id),
            after_data={"team_a_score": a, "team_b_score": b, "winner": str(match.winner_team_id)},
            ip_address=meta.get("ip_address"), user_agent=meta.get("user_agent"),
        )
        self._after_result(match, tournament)
        self.db.commit()
        self.db.refresh(match)
        return match

    def correct_match(
        self, *, match_id: uuid.UUID, a: int, b: int, expected_version: int, reason: str,
        reset_dependents: bool, actor: User, meta: dict,
    ) -> Match:
        match = self.get_match(match_id)
        if match.status != MatchStatus.COMPLETED:
            raise errors.match_not_editable("Only a completed match can be corrected.")
        self._check_version(match, expected_version)

        before = {
            "team_a_score": match.team_a_score,
            "team_b_score": match.team_b_score,
            "winner": str(match.winner_team_id),
        }
        tournament = self._tournament(match)
        side = self._resolve(tournament, a, b)
        old_winner = match.winner_team_id
        self._apply_result(match, a, b, side)
        match.version += 1
        match.updated_by = actor.id

        self.audit.record(
            actor_user_id=actor.id, action="match.correct", entity_type="match",
            entity_id=str(match.id), before_data=before,
            after_data={"team_a_score": a, "team_b_score": b, "winner": str(match.winner_team_id)},
            reason=reason, severity=AuditSeverity.WARNING,
            ip_address=meta.get("ip_address"), user_agent=meta.get("user_agent"),
        )
        self._after_correction(match, tournament, old_winner, reset_dependents, actor, meta)
        self.db.commit()
        self.db.refresh(match)
        return match

    # -- post-result hooks (bracket propagation added in Phase 5) ----------

    def _after_result(self, match: Match, tournament: Tournament) -> None:
        if match.stage == MatchStage.GROUP:
            self._maybe_complete_group(tournament)
            return
        # Bracket match completed: propagate winner/loser into dependent slots.
        from app.services.bracket_service import BracketService

        BracketService(self.db).propagate_from(match)
        if match.stage == MatchStage.FINAL:
            tournament.status = TournamentStatus.COMPLETED

    def _after_correction(
        self, match: Match, tournament: Tournament, old_winner: uuid.UUID | None,
        reset_dependents: bool, actor: User, meta: dict,
    ) -> None:
        # Group corrections only affect standings, computed on demand.
        if match.stage == MatchStage.GROUP:
            return
        # Bracket: if the winner (hence the propagated participant) didn't change,
        # downstream is unaffected.
        if match.winner_team_id == old_winner:
            return

        from app.services.bracket_service import BracketService

        bracket = BracketService(self.db)
        dependents = bracket._dependents_of(match)
        if not dependents:
            return
        if bracket.has_started_dependents(match) and not reset_dependents:
            raise errors.dependent_match_already_started()
        # Safe: reset downstream, then re-propagate from the corrected result.
        bracket.reset_cascade(match, actor, meta)
        bracket.propagate_from(match)

    def _maybe_complete_group(self, tournament: Tournament) -> None:
        if tournament.status not in (TournamentStatus.GROUP_IN_PROGRESS, TournamentStatus.SCHEDULED):
            return
        # Flush so the just-completed match is visible to the count (autoflush=False).
        self.db.flush()
        remaining = self.db.execute(
            select(func.count()).select_from(Match).where(
                Match.tournament_id == tournament.id,
                Match.stage == MatchStage.GROUP,
                Match.status != MatchStatus.COMPLETED,
            )
        ).scalar_one()
        if remaining == 0:
            tournament.status = TournamentStatus.GROUP_COMPLETE
