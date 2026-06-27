import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user, get_request_meta, is_admin_user, require_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.mappers import to_team_out
from app.schemas.team import AddMemberRequest, TeamCreate, TeamOut, TeamUpdate
from app.services.team_service import TeamService
from app.services.tournament_service import TournamentService

router = APIRouter(prefix="/tournaments/{tournament_id}/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def list_teams(
    tournament_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[TeamOut]:
    # Enforce tournament visibility before exposing its teams.
    TournamentService(db).get_visible(tournament_id, is_admin=is_admin_user(viewer))
    teams = TeamService(db).list_teams(tournament_id)
    return [to_team_out(t) for t in teams]


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    tournament_id: uuid.UUID,
    body: TeamCreate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TeamOut:
    team = TeamService(db).create_team(
        tournament_id=tournament_id,
        name=body.name,
        initial_seed=body.initial_seed,
        logo_url=body.logo_url,
        actor=actor,
        meta=meta,
    )
    return to_team_out(team)


@router.patch("/{team_id}", response_model=TeamOut)
def update_team(
    tournament_id: uuid.UUID,
    team_id: uuid.UUID,
    body: TeamUpdate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TeamOut:
    team = TeamService(db).update_team(
        tournament_id=tournament_id,
        team_id=team_id,
        name=body.name,
        initial_seed=body.initial_seed,
        logo_url=body.logo_url,
        actor=actor,
        meta=meta,
    )
    return to_team_out(team)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    tournament_id: uuid.UUID,
    team_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> None:
    TeamService(db).delete_team(tournament_id=tournament_id, team_id=team_id, actor=actor, meta=meta)


@router.post("/{team_id}/members", response_model=TeamOut)
def add_member(
    tournament_id: uuid.UUID,
    team_id: uuid.UUID,
    body: AddMemberRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TeamOut:
    team = TeamService(db).add_member(
        tournament_id=tournament_id,
        team_id=team_id,
        player_id=body.player_id,
        actor=actor,
        meta=meta,
    )
    return to_team_out(team)


@router.delete("/{team_id}/members/{player_id}", response_model=TeamOut)
def remove_member(
    tournament_id: uuid.UUID,
    team_id: uuid.UUID,
    player_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TeamOut:
    team = TeamService(db).remove_member(
        tournament_id=tournament_id,
        team_id=team_id,
        player_id=player_id,
        actor=actor,
        meta=meta,
    )
    return to_team_out(team)
