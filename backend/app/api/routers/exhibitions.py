import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_request_meta, require_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.exhibition import ExhibitionCreate
from app.schemas.mappers import to_match_out
from app.schemas.match import MatchOut
from app.services.exhibition_service import ExhibitionService

router = APIRouter(prefix="/exhibitions", tags=["exhibitions"])


@router.get("", response_model=list[MatchOut])
def list_exhibitions(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[MatchOut]:
    return [to_match_out(m) for m in ExhibitionService(db).list_matches()]


@router.post("", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
def create_exhibition(
    body: ExhibitionCreate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> MatchOut:
    match = ExhibitionService(db).create(
        label=body.label,
        team_a_name=body.team_a.name,
        team_a_players=body.team_a.player_ids,
        team_b_name=body.team_b.name,
        team_b_players=body.team_b.player_ids,
        target_points=body.target_points,
        win_by_two=body.win_by_two,
        actor=actor,
        meta=meta,
    )
    return to_match_out(match)


@router.get("/{match_id}", response_model=MatchOut)
def get_exhibition(
    match_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MatchOut:
    return to_match_out(ExhibitionService(db).get_match(match_id))
