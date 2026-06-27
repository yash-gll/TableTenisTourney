import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import ApprovalStatus, MatchStatus
from app.db.models.match import Match
from app.db.models.player_profile import PlayerProfile
from app.db.models.team_member import TeamMember
from app.db.models.tournament_result import TournamentResult
from app.db.models.user import User
from app.domain.achievements import AchievementInput, Badge, earned_badges
from app.schemas.player import PlayerStatsOut, ProfileUpdate


class PlayerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_profile(self, *, user: User, data: ProfileUpdate) -> PlayerProfile:
        profile = user.profile
        if data.display_name is not None:
            profile.display_name = data.display_name.strip()
        if data.bio is not None:
            profile.bio = data.bio
        self.db.commit()
        self.db.refresh(profile)
        return profile

    # -- public directory --------------------------------------------------

    def search(self, *, query: str | None, limit: int = 100) -> list[PlayerProfile]:
        stmt = select(PlayerProfile).where(
            PlayerProfile.approval_status == ApprovalStatus.APPROVED
        )
        if query:
            stmt = stmt.where(PlayerProfile.display_name.ilike(f"%{query.strip()}%"))
        stmt = stmt.order_by(
            PlayerProfile.current_rating.desc(), PlayerProfile.display_name
        ).limit(limit)
        return list(self.db.execute(stmt).scalars())

    def get_profile(self, player_id: uuid.UUID) -> PlayerProfile:
        profile = self.db.get(PlayerProfile, player_id)
        if profile is None:
            raise errors.player_not_found()
        return profile

    def stats(self, player_id: uuid.UUID) -> PlayerStatsOut:
        team_ids = list(
            self.db.execute(
                select(TeamMember.team_id).where(TeamMember.player_id == player_id)
            ).scalars()
        )
        tournaments_played = self.db.execute(
            select(func.count(func.distinct(TeamMember.tournament_id))).where(
                TeamMember.player_id == player_id
            )
        ).scalar_one()

        if not team_ids:
            return PlayerStatsOut(
                matches_played=0, wins=0, losses=0, win_pct=0.0,
                tournaments_played=int(tournaments_played), tournament_wins=0,
            )

        played = self.db.execute(
            select(func.count()).select_from(Match).where(
                Match.status == MatchStatus.COMPLETED,
                or_(Match.team_a_id.in_(team_ids), Match.team_b_id.in_(team_ids)),
            )
        ).scalar_one()
        wins = self.db.execute(
            select(func.count()).select_from(Match).where(
                Match.status == MatchStatus.COMPLETED,
                Match.winner_team_id.in_(team_ids),
            )
        ).scalar_one()
        tournament_wins = self.db.execute(
            select(func.count()).select_from(TournamentResult).where(
                TournamentResult.champion_team_id.in_(team_ids)
            )
        ).scalar_one()

        losses = int(played) - int(wins)
        win_pct = round(int(wins) / int(played) * 100, 1) if played else 0.0
        return PlayerStatsOut(
            matches_played=int(played),
            wins=int(wins),
            losses=losses,
            win_pct=win_pct,
            tournaments_played=int(tournaments_played),
            tournament_wins=int(tournament_wins),
        )

    def achievements(self, player_id: uuid.UUID) -> list[Badge]:
        team_ids = list(
            self.db.execute(
                select(TeamMember.team_id).where(TeamMember.player_id == player_id)
            ).scalars()
        )
        if not team_ids:
            return earned_badges(AchievementInput(0, 0, 0, 0, 0, 0))

        results = self.db.execute(
            select(TournamentResult).where(
                or_(
                    TournamentResult.champion_team_id.in_(team_ids),
                    TournamentResult.runner_up_team_id.in_(team_ids),
                    TournamentResult.third_place_team_id.in_(team_ids),
                    TournamentResult.fourth_place_team_id.in_(team_ids),
                )
            )
        ).scalars().all()
        titles = sum(1 for r in results if r.champion_team_id in team_ids)
        finals = sum(
            1 for r in results
            if r.champion_team_id in team_ids or r.runner_up_team_id in team_ids
        )
        podiums = len(results)

        matches = self.db.execute(
            select(Match).where(
                Match.status == MatchStatus.COMPLETED,
                or_(Match.team_a_id.in_(team_ids), Match.team_b_id.in_(team_ids)),
            ).order_by(Match.completed_at)
        ).scalars().all()
        played = len(matches)
        wins = 0
        streak = longest = 0
        for m in matches:
            if m.winner_team_id in team_ids:
                wins += 1
                streak += 1
                longest = max(longest, streak)
            else:
                streak = 0

        return earned_badges(
            AchievementInput(
                titles=titles, finals_reached=finals, podiums=podiums,
                matches_played=played, wins=wins, longest_win_streak=longest,
            )
        )
