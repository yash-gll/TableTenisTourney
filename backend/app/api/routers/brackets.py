import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user, get_request_meta, is_admin_user, require_admin
from app.db.models.team import Team
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.bracket import BracketOut, PlacementOut
from app.schemas.mappers import to_match_out
from app.services.bracket_service import BracketService
from app.services.tournament_service import TournamentService

router = APIRouter(prefix="/tournaments/{tournament_id}/bracket", tags=["bracket"])


def _team_names(db: Session, tournament_id: uuid.UUID) -> dict[str, str]:
    teams = db.execute(select(Team).where(Team.tournament_id == tournament_id)).scalars()
    return {str(t.id): t.name for t in teams}


def _bracket_out(db: Session, tournament_id: uuid.UUID) -> BracketOut:
    matches, placements = BracketService(db).get_bracket(tournament_id)
    names = _team_names(db, tournament_id)
    placement_out = [
        PlacementOut(place=place, team_id=uuid.UUID(tid), team_name=names.get(tid, "?"))
        for tid, place in sorted(placements.items(), key=lambda kv: kv[1])
    ]
    return BracketOut(matches=[to_match_out(m) for m in matches], placements=placement_out)


@router.post("/generate", response_model=BracketOut)
def generate_bracket(
    tournament_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> BracketOut:
    BracketService(db).generate(tournament_id=tournament_id, actor=actor, meta=meta)
    return _bracket_out(db, tournament_id)


@router.get("", response_model=BracketOut)
def get_bracket(
    tournament_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> BracketOut:
    TournamentService(db).get_visible(tournament_id, is_admin=is_admin_user(viewer))
    return _bracket_out(db, tournament_id)


@router.post("/rebuild", response_model=BracketOut)
def rebuild_bracket(
    tournament_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> BracketOut:
    BracketService(db).rebuild(tournament_id=tournament_id, actor=actor, meta=meta)
    return _bracket_out(db, tournament_id)
