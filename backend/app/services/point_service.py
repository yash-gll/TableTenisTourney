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

    def _live_score(self, match: Match) -> dict:
        """Recompute the running tally and mirror it onto the match row so every
        viewer polling the match list sees the live score, not just the logger."""
        score = self.running_score(match.id)
        match.team_a_score = score["team_a"]
        match.team_b_score = score["team_b"]
        return score

    def log_point(
        self, *, match_id: uuid.UUID, player_id: uuid.UUID, skill: str, kind: str = "WIN", actor
    ) -> dict:
        match = self._match(match_id)
        if match.status in (MatchStatus.COMPLETED, MatchStatus.CANCELLED, MatchStatus.VOID):
            raise errors.match_not_editable("This match is closed.")
        if match.team_a_id is None or match.team_b_id is None:
            raise errors.match_not_editable("Both teams must be set.")

        kind = kind.upper()
        if kind not in ("WIN", "FAULT"):
            raise errors.invalid_skill_rating(f"Unknown point kind '{kind}'.")
        if kind == "WIN":
            if skill not in skills_domain.SKILL_KEYS:
                raise errors.invalid_skill_rating(f"Unknown skill '{skill}'.")
            mapped_skill = skill
        else:
            if skill not in skills_domain.FAULT_KEYS:
                raise errors.invalid_skill_rating(f"Unknown fault '{skill}'.")
            mapped_skill = skills_domain.FAULT_SKILL[skill]

        # The player must belong to one of the two teams (find which).
        player_team = self.db.execute(
            select(TeamMember.team_id).where(
                TeamMember.player_id == player_id,
                TeamMember.team_id.in_([match.team_a_id, match.team_b_id]),
            )
        ).scalar_one_or_none()
        if player_team is None:
            raise errors.invalid_prediction()  # player not in this match

        # A winning shot scores for the player's team; a fault gifts the point
        # to the opponent (but is still attributed to the erring player).
        if kind == "WIN":
            scoring_team = player_team
        else:
            scoring_team = (
                match.team_b_id if player_team == match.team_a_id else match.team_a_id
            )

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
                team_id=scoring_team,
                player_id=player_id,
                skill=mapped_skill,
                kind=kind,
            )
        )
        self.db.flush()
        score = self._live_score(match)
        self.db.commit()
        return score

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
            self.db.flush()
        score = self._live_score(match)
        self.db.commit()
        return score

    # -- skill derivation --------------------------------------------------

    def recompute_player_skills(self, player_id: uuid.UUID) -> None:
        """Recompute a player's skills from points won in COMPLETED matches,
        leaving any admin-pinned skills untouched."""
        profile = self.db.get(PlayerProfile, player_id)
        if profile is None:
            return
        rows = self.db.execute(
            select(MatchPoint.skill, MatchPoint.kind, func.count())
            .join(Match, Match.id == MatchPoint.match_id)
            .where(
                MatchPoint.player_id == player_id,
                Match.status == MatchStatus.COMPLETED,
            )
            .group_by(MatchPoint.skill, MatchPoint.kind)
        ).all()
        wins: dict[str, int] = {}
        errors_: dict[str, int] = {}
        for skill, kind, count in rows:
            (wins if kind == "WIN" else errors_)[skill] = int(count)
        pinned = profile.skill_overrides or {}
        ratings = dict(profile.skill_ratings or {})
        for key, _label in skills_domain.SKILL_ATTRIBUTES:
            if key in pinned:
                continue
            ratings[key] = derived_skill(wins.get(key, 0), errors_.get(key, 0))
        profile.skill_ratings = ratings

    def recompute_for_match(self, match: Match) -> None:
        player_ids = self.db.execute(
            select(MatchPoint.player_id).where(MatchPoint.match_id == match.id).distinct()
        ).scalars().all()
        for pid in player_ids:
            self.recompute_player_skills(pid)
        self.db.flush()
