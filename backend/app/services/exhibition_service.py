import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import (
    ApprovalStatus,
    MatchStage,
    MatchStatus,
    TournamentStatus,
    TournamentVisibility,
)
from app.db.models.match import Match
from app.db.models.player_profile import PlayerProfile
from app.db.models.team import Team
from app.db.models.team_member import TeamMember
from app.db.models.tournament import Tournament
from app.db.models.user import User
from app.services.audit_service import AuditService
from app.services.schedule_service import pair_key
from app.services.tournament_service import _slugify

TEAM_MAX = 2


class ExhibitionService:
    """A standalone match outside any tournament. It is backed by its own hidden
    ``is_exhibition`` tournament container so it reuses all of the existing
    scoring / Elo / point-logging / skill machinery, but never appears in
    tournament lists, tables, or predictions."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    # -- reads -------------------------------------------------------------

    def list_matches(self) -> list[Match]:
        return list(
            self.db.execute(
                select(Match)
                .join(Tournament, Tournament.id == Match.tournament_id)
                .where(Tournament.is_exhibition.is_(True))
                .order_by(Match.created_at.desc())
            ).scalars()
        )

    def rosters(self, matches: list[Match]) -> dict[uuid.UUID, list[str]]:
        """team_id -> ordered player display names, for the given matches."""
        team_ids = {m.team_a_id for m in matches} | {m.team_b_id for m in matches}
        team_ids.discard(None)
        if not team_ids:
            return {}
        result: dict[uuid.UUID, list[str]] = {}
        rows = self.db.execute(
            select(TeamMember.team_id, PlayerProfile.display_name)
            .join(PlayerProfile, PlayerProfile.id == TeamMember.player_id)
            .where(TeamMember.team_id.in_(team_ids))
            .order_by(TeamMember.team_id, TeamMember.member_order)
        ).all()
        for team_id, name in rows:
            result.setdefault(team_id, []).append(name)
        return result

    def get_match(self, match_id: uuid.UUID) -> Match:
        match = self.db.get(Match, match_id)
        if match is None:
            raise errors.match_not_found()
        t = self.db.get(Tournament, match.tournament_id)
        if t is None or not t.is_exhibition:
            raise errors.match_not_found()
        return match

    # -- create ------------------------------------------------------------

    def _resolve_roster(self, player_ids: list[uuid.UUID]) -> list[PlayerProfile]:
        if not 1 <= len(player_ids) <= TEAM_MAX:
            raise errors.invalid_exhibition(f"Each side needs 1–{TEAM_MAX} players.")
        profiles = []
        for pid in player_ids:
            profile = self.db.get(PlayerProfile, pid)
            if profile is None:
                raise errors.player_not_found()
            if profile.approval_status != ApprovalStatus.APPROVED:
                raise errors.player_not_approved()
            profiles.append(profile)
        return profiles

    def create(
        self,
        *,
        label: str | None,
        team_a_name: str,
        team_a_players: list[uuid.UUID],
        team_b_name: str,
        team_b_players: list[uuid.UUID],
        target_points: int,
        win_by_two: bool,
        actor: User,
        meta: dict,
    ) -> Match:
        team_a_name = team_a_name.strip()
        team_b_name = team_b_name.strip()
        if not team_a_name or not team_b_name:
            raise errors.invalid_exhibition("Both teams need a name.")
        if team_a_name.lower() == team_b_name.lower():
            raise errors.invalid_exhibition("The two teams need different names.")

        a_profiles = self._resolve_roster(team_a_players)
        b_profiles = self._resolve_roster(team_b_players)
        a_ids = {p.id for p in a_profiles}
        b_ids = {p.id for p in b_profiles}
        if a_ids & b_ids:
            raise errors.invalid_exhibition("A player can't be on both sides.")

        name = (label or "").strip() or f"{team_a_name} vs {team_b_name}"
        tournament = Tournament(
            name=name,
            slug=_slugify(name),
            visibility=TournamentVisibility.PRIVATE,
            status=TournamentStatus.SCHEDULED,
            is_exhibition=True,
            target_points=target_points,
            win_by_two=win_by_two,
            created_by=actor.id,
            version=1,
        )
        self.db.add(tournament)
        self.db.flush()

        teams = []
        for tname, profiles in ((team_a_name, a_profiles), (team_b_name, b_profiles)):
            team = Team(tournament_id=tournament.id, name=tname, created_by=actor.id)
            self.db.add(team)
            self.db.flush()
            for order, profile in enumerate(profiles, start=1):
                self.db.add(
                    TeamMember(
                        tournament_id=tournament.id,
                        team_id=team.id,
                        player_id=profile.id,
                        member_order=order,
                    )
                )
            teams.append(team)

        match = Match(
            tournament_id=tournament.id,
            stage=MatchStage.GROUP,
            round_number=1,
            display_order=1,
            team_a_id=teams[0].id,
            team_b_id=teams[1].id,
            status=MatchStatus.SCHEDULED,
            pair_key=pair_key(teams[0].id, teams[1].id),
            created_by=actor.id,
        )
        self.db.add(match)
        self.db.flush()

        # Baseline snapshot so a later score correction can replay Elo cleanly.
        from app.services.rating_service import RatingService

        RatingService(self.db).snapshot_start(tournament.id)

        self.audit.record(
            actor_user_id=actor.id,
            action="exhibition.create",
            entity_type="match",
            entity_id=str(match.id),
            after_data={"name": name, "tournament_id": str(tournament.id)},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(match)
        return match
