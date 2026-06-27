import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user, get_request_meta, is_admin_user, require_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.mappers import to_match_out, to_tournament_out
from app.schemas.match import MatchOut, ScheduleGenerateResponse
from app.schemas.tournament import (
    TournamentCreate,
    TournamentOut,
    TournamentUpdate,
    TransitionRequest,
)
from app.services.schedule_service import ScheduleService
from app.services.tournament_service import TournamentService

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.get("", response_model=list[TournamentOut])
def list_tournaments(
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[TournamentOut]:
    service = TournamentService(db)
    if is_admin_user(viewer):
        items = service.list_visible(is_admin=True)
    elif viewer is not None and viewer.profile is not None:
        # Players see only started tournaments they participate in.
        items = service.list_for_player(viewer.profile.id)
    else:
        items = service.list_visible(is_admin=False)
    return [to_tournament_out(t) for t in items]


@router.get("/{tournament_id}", response_model=TournamentOut)
def get_tournament(
    tournament_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> TournamentOut:
    t = TournamentService(db).get_visible(tournament_id, is_admin=is_admin_user(viewer))
    return to_tournament_out(t)


@router.post("", response_model=TournamentOut, status_code=status.HTTP_201_CREATED)
def create_tournament(
    body: TournamentCreate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TournamentOut:
    t = TournamentService(db).create(data=body, actor=actor, meta=meta)
    return to_tournament_out(t)


@router.patch("/{tournament_id}", response_model=TournamentOut)
def update_tournament(
    tournament_id: uuid.UUID,
    body: TournamentUpdate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TournamentOut:
    t = TournamentService(db).update(tournament_id=tournament_id, data=body, actor=actor, meta=meta)
    return to_tournament_out(t)


@router.post("/{tournament_id}/transition", response_model=TournamentOut)
def transition_tournament(
    tournament_id: uuid.UUID,
    body: TransitionRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TournamentOut:
    t = TournamentService(db).transition(
        tournament_id=tournament_id, target=body.target, reason=body.reason, actor=actor, meta=meta
    )
    return to_tournament_out(t)


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament(
    tournament_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> None:
    TournamentService(db).delete(tournament_id=tournament_id, actor=actor, meta=meta)


@router.post("/{tournament_id}/finalize", response_model=TournamentOut)
def finalize_tournament(
    tournament_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TournamentOut:
    t = TournamentService(db).finalize(tournament_id=tournament_id, actor=actor, meta=meta)
    return to_tournament_out(t)


@router.post("/{tournament_id}/reopen", response_model=TournamentOut)
def reopen_tournament(
    tournament_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> TournamentOut:
    t = TournamentService(db).reopen(tournament_id=tournament_id, actor=actor, meta=meta)
    return to_tournament_out(t)


@router.post("/{tournament_id}/schedule/generate", response_model=ScheduleGenerateResponse)
def generate_schedule(
    tournament_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> ScheduleGenerateResponse:
    count, rounds = ScheduleService(db).generate(tournament_id=tournament_id, actor=actor, meta=meta)
    return ScheduleGenerateResponse(match_count=count, rounds=rounds)


@router.get("/{tournament_id}/matches", response_model=list[MatchOut])
def list_matches(
    tournament_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[MatchOut]:
    TournamentService(db).get_visible(tournament_id, is_admin=is_admin_user(viewer))
    matches = ScheduleService(db).list_matches(tournament_id)
    return [to_match_out(m) for m in matches]
