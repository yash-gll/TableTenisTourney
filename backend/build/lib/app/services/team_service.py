import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import ApprovalStatus
from app.db.models.player_profile import PlayerProfile
from app.db.models.team import Team
from app.db.models.team_member import TeamMember
from app.db.models.tournament import Tournament
from app.db.models.user import User
from app.domain import tournament_state
from app.services.audit_service import AuditService

MAX_TEAM_SIZE = 2


class TeamService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    # -- helpers -----------------------------------------------------------

    def _get_tournament(self, tournament_id: uuid.UUID) -> Tournament:
        t = self.db.get(Tournament, tournament_id)
        if t is None:
            raise errors.tournament_not_found()
        return t

    def _require_editable(self, tournament: Tournament) -> None:
        if not tournament_state.is_editable(tournament.status):
            raise errors.tournament_not_editable()

    def _get_team(self, tournament_id: uuid.UUID, team_id: uuid.UUID) -> Team:
        team = self.db.get(Team, team_id)
        if team is None or team.tournament_id != tournament_id:
            raise errors.team_not_found()
        return team

    def _name_exists(self, tournament_id: uuid.UUID, name: str, exclude_team: uuid.UUID | None) -> bool:
        stmt = select(Team).where(Team.tournament_id == tournament_id, Team.name == name)
        if exclude_team is not None:
            stmt = stmt.where(Team.id != exclude_team)
        return self.db.execute(stmt).first() is not None

    # -- reads -------------------------------------------------------------

    def list_teams(self, tournament_id: uuid.UUID) -> list[Team]:
        self._get_tournament(tournament_id)
        stmt = (
            select(Team)
            .where(Team.tournament_id == tournament_id)
            .order_by(Team.created_at)
        )
        return list(self.db.execute(stmt).scalars())

    # -- team writes -------------------------------------------------------

    def create_team(self, *, tournament_id: uuid.UUID, name: str, initial_seed: int | None,
                     logo_url: str | None, actor: User, meta: dict) -> Team:
        tournament = self._get_tournament(tournament_id)
        self._require_editable(tournament)
        name = name.strip()
        if self._name_exists(tournament_id, name, None):
            raise errors.team_name_taken(name)

        team = Team(
            tournament_id=tournament_id,
            name=name,
            initial_seed=initial_seed,
            logo_url=logo_url,
            created_by=actor.id,
        )
        self.db.add(team)
        self.db.flush()
        self.audit.record(
            actor_user_id=actor.id,
            action="team.create",
            entity_type="team",
            entity_id=str(team.id),
            after_data={"name": team.name, "tournament_id": str(tournament_id)},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(team)
        return team

    def update_team(self, *, tournament_id: uuid.UUID, team_id: uuid.UUID, name: str | None,
                    initial_seed: int | None, logo_url: str | None, actor: User, meta: dict) -> Team:
        tournament = self._get_tournament(tournament_id)
        self._require_editable(tournament)
        team = self._get_team(tournament_id, team_id)

        if name is not None:
            name = name.strip()
            if name != team.name and self._name_exists(tournament_id, name, team_id):
                raise errors.team_name_taken(name)
            team.name = name
        if initial_seed is not None:
            team.initial_seed = initial_seed
        if logo_url is not None:
            team.logo_url = logo_url

        self.audit.record(
            actor_user_id=actor.id,
            action="team.update",
            entity_type="team",
            entity_id=str(team.id),
            after_data={"name": team.name, "initial_seed": team.initial_seed},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(team)
        return team

    def delete_team(self, *, tournament_id: uuid.UUID, team_id: uuid.UUID, actor: User,
                    meta: dict) -> None:
        tournament = self._get_tournament(tournament_id)
        self._require_editable(tournament)
        team = self._get_team(tournament_id, team_id)
        self.audit.record(
            actor_user_id=actor.id,
            action="team.delete",
            entity_type="team",
            entity_id=str(team.id),
            before_data={"name": team.name},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.delete(team)
        self.db.commit()

    # -- roster writes -----------------------------------------------------

    def add_member(self, *, tournament_id: uuid.UUID, team_id: uuid.UUID, player_id: uuid.UUID,
                   actor: User, meta: dict) -> Team:
        tournament = self._get_tournament(tournament_id)
        self._require_editable(tournament)
        team = self._get_team(tournament_id, team_id)

        profile = self.db.get(PlayerProfile, player_id)
        if profile is None:
            raise errors.player_not_found()
        if profile.approval_status != ApprovalStatus.APPROVED:
            raise errors.player_not_approved()

        # Already on a team in this tournament?
        existing = self.db.execute(
            select(TeamMember).where(
                TeamMember.tournament_id == tournament_id, TeamMember.player_id == player_id
            )
        ).first()
        if existing is not None:
            raise errors.player_already_on_team()

        if len(team.members) >= MAX_TEAM_SIZE:
            raise errors.team_already_full()

        used_orders = {m.member_order for m in team.members}
        member_order = next(o for o in range(1, MAX_TEAM_SIZE + 1) if o not in used_orders)

        member = TeamMember(
            tournament_id=tournament_id,
            team_id=team_id,
            player_id=player_id,
            member_order=member_order,
        )
        self.db.add(member)
        self.audit.record(
            actor_user_id=actor.id,
            action="team.member_add",
            entity_type="team",
            entity_id=str(team.id),
            after_data={"player_id": str(player_id), "member_order": member_order},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(team)
        return team

    def remove_member(self, *, tournament_id: uuid.UUID, team_id: uuid.UUID, player_id: uuid.UUID,
                      actor: User, meta: dict) -> Team:
        tournament = self._get_tournament(tournament_id)
        self._require_editable(tournament)
        team = self._get_team(tournament_id, team_id)

        member = self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id, TeamMember.player_id == player_id
            )
        ).scalar_one_or_none()
        if member is None:
            raise errors.player_not_found()

        self.db.delete(member)
        self.audit.record(
            actor_user_id=actor.id,
            action="team.member_remove",
            entity_type="team",
            entity_id=str(team.id),
            before_data={"player_id": str(player_id)},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(team)
        return team
