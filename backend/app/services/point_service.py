import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import MatchStage, MatchStatus, TournamentStatus
from app.db.models.match import Match
from app.db.models.match_point import MatchPoint
from app.db.models.player_profile import PlayerProfile
from app.db.models.team_member import TeamMember
from app.domain import skills as skills_domain
from app.domain.skills import derived_skill


class PointService:
    """Live point-by-point logging and play-derived skill recomputation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _match(self, match_id: uuid.UUID) -> Match:
        m = self.db.get(Match, match_id)
        if m is None:
            raise errors.match_not_found()
        return m

    def running_score(self, match_id: uuid.UUID) -> dict:
        m = self._match(match_id)
        rows = self.db.execute(
            select(MatchPoint.team_id, func.count())
            .where(MatchPoint.match_id == match_id)
            .group_by(MatchPoint.team_id)
        ).all()
        counts = {tid: int(c) for tid, c in rows}
        return {
            "team_a": counts.get(m.team_a_id, 0),
            "team_b": counts.get(m.team_b_id, 0),
        }

    def log_point(
        self, *, match_id: uuid.UUID, player_id: uuid.UUID, skill: str, actor
    ) -> dict:
        match = self._match(match_id)
        if match.status in (MatchStatus.COMPLETED, MatchStatus.CANCELLED, MatchStatus.VOID):
            raise errors.match_not_editable("This match is closed.")
        if skill not in skills_domain.SKILL_KEYS:
            raise errors.invalid_skill_rating(f"Unknown skill '{skill}'.")
        if match.team_a_id is None or match.team_b_id is None:
            raise errors.match_not_editable("Both teams must be set.")

        # The player must belong to one of the two teams (find which).
        team_id = self.db.execute(
            select(TeamMember.team_id).where(
                TeamMember.player_id == player_id,
                TeamMember.team_id.in_([match.team_a_id, match.team_b_id]),
            )
        ).scalar_one_or_none()
        if team_id is None:
            raise errors.invalid_prediction()  # player not in this match

        # First point auto-starts the match.
        if match.status == MatchStatus.SCHEDULED:
            from app.db.models.tournament import Tournament

            match.status = MatchStatus.IN_PROGRESS
            t = self.db.get(Tournament, match.tournament_id)
            if t and match.stage == MatchStage.GROUP and t.status == TournamentStatus.SCHEDULED:
                t.status = TournamentStatus.GROUP_IN_PROGRESS
            match.version += 1
            if actor is not None:
                match.updated_by = actor.id

        self.db.add(
            MatchPoint(
                match_id=match_id,
                tournament_id=match.tournament_id,
                team_id=team_id,
                player_id=player_id,
                skill=skill,
            )
        )
        self.db.commit()
        return self.running_score(match_id)

    def undo_last(self, *, match_id: uuid.UUID) -> dict:
        match = self._match(match_id)
        if match.status == MatchStatus.COMPLETED:
            raise errors.match_not_editable("This match is already final.")
        last = self.db.execute(
            select(MatchPoint)
            .where(MatchPoint.match_id == match_id)
            .order_by(MatchPoint.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if last is not None:
            self.db.delete(last)
            self.db.commit()
        return self.running_score(match_id)

    # -- skill derivation --------------------------------------------------

    def recompute_player_skills(self, player_id: uuid.UUID) -> None:
        """Recompute a player's skills from points won in COMPLETED matches,
        leaving any admin-pinned skills untouched."""
        profile = self.db.get(PlayerProfile, player_id)
        if profile is None:
            return
        rows = self.db.execute(
            select(MatchPoint.skill, func.count())
            .join(Match, Match.id == MatchPoint.match_id)
            .where(
                MatchPoint.player_id == player_id,
                Match.status == MatchStatus.COMPLETED,
            )
            .group_by(MatchPoint.skill)
        ).all()
        counts = {skill: int(c) for skill, c in rows}
        pinned = profile.skill_overrides or {}
        ratings = dict(profile.skill_ratings or {})
        for key, _label in skills_domain.SKILL_ATTRIBUTES:
            if key in pinned:
                continue
            ratings[key] = derived_skill(counts.get(key, 0))
        profile.skill_ratings = ratings

    def recompute_for_match(self, match: Match) -> None:
        player_ids = self.db.execute(
            select(MatchPoint.player_id).where(MatchPoint.match_id == match.id).distinct()
        ).scalars().all()
        for pid in player_ids:
            self.recompute_player_skills(pid)
        self.db.flush()
