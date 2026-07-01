import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user, get_request_meta, is_admin_user, require_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.mappers import to_match_out
from app.schemas.match import CompleteRequest, CorrectRequest, MatchOut, ServePairingRequest
from app.services.scoring_service import ScoringService
from app.services.tournament_service import TournamentService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/{match_id}", response_model=MatchOut)
def get_match(
    match_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> MatchOut:
    match = ScoringService(db).get_match(match_id)
    TournamentService(db).get_visible(match.tournament_id, is_admin=is_admin_user(viewer))
    return to_match_out(match)


@router.post("/{match_id}/start", response_model=MatchOut)
def start_match(
    match_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> MatchOut:
    return to_match_out(ScoringService(db).start_match(match_id=match_id, actor=actor, meta=meta))


@router.put("/{match_id}/serve-pairing", response_model=MatchOut)
def set_serve_pairing(
    match_id: uuid.UUID,
    body: ServePairingRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MatchOut:
    match = ScoringService(db).set_serve_pairing(
        match_id=match_id, pairing=body.pairing, first_server_id=body.first_server_id, actor=actor
    )
    return to_match_out(match)


@router.post("/{match_id}/complete", response_model=MatchOut)
def complete_match(
    match_id: uuid.UUID,
    body: CompleteRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> MatchOut:
    match = ScoringService(db).complete_match(
        match_id=match_id,
        a=body.team_a_score,
        b=body.team_b_score,
        expected_version=body.expected_version,
        actor=actor,
        meta=meta,
    )
    return to_match_out(match)


@router.post("/{match_id}/correct", response_model=MatchOut)
def correct_match(
    match_id: uuid.UUID,
    body: CorrectRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> MatchOut:
    match = ScoringService(db).correct_match(
        match_id=match_id,
        a=body.team_a_score,
        b=body.team_b_score,
        expected_version=body.expected_version,
        reason=body.reason,
        reset_dependents=body.reset_dependents,
        actor=actor,
        meta=meta,
    )
    return to_match_out(match)
