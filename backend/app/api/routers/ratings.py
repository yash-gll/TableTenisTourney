import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import errors
from app.core.deps import get_request_meta, require_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import MessageResponse
from app.schemas.rating import (
    RatingAdjustment,
    RatingConfigOut,
    RatingConfigUpdate,
    RatingEventOut,
    RecalculateRequest,
)
from app.services.audit_service import AuditService
from app.services.rating_service import RatingService

router = APIRouter(tags=["ratings"])


@router.get("/ratings/config", response_model=RatingConfigOut)
def get_config(db: Session = Depends(get_db)) -> RatingConfigOut:
    cfg = RatingService(db).get_config()
    return RatingConfigOut(**cfg.__dict__)


@router.patch("/admin/ratings/config", response_model=RatingConfigOut)
def update_config(
    body: RatingConfigUpdate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RatingConfigOut:
    row = RatingService(db).get_config_row()
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.commit()
    cfg = RatingService(db).get_config()
    return RatingConfigOut(**cfg.__dict__)


@router.get("/players/{player_id}/rating-events", response_model=list[RatingEventOut])
def player_rating_events(player_id: uuid.UUID, db: Session = Depends(get_db)) -> list[RatingEventOut]:
    events = RatingService(db).player_events(player_id)
    return [
        RatingEventOut(
            id=e.id, tournament_id=e.tournament_id, match_id=e.match_id,
            event_type=e.event_type.value, rating_before=e.rating_before, delta=e.delta,
            rating_after=e.rating_after, reason=e.reason, created_at=e.created_at,
        )
        for e in events
    ]


@router.post("/admin/players/{player_id}/rating-adjustment", response_model=MessageResponse)
def rating_adjustment(
    player_id: uuid.UUID,
    body: RatingAdjustment,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> MessageResponse:
    profile = RatingService(db).admin_adjust(
        player_id=player_id, delta=body.delta, reason=body.reason
    )
    if profile is None:
        raise errors.player_not_found()
    AuditService(db).record(
        actor_user_id=actor.id, action="rating.admin_adjustment", entity_type="player_profile",
        entity_id=str(player_id), after_data={"delta": body.delta}, reason=body.reason,
        ip_address=meta.get("ip_address"), user_agent=meta.get("user_agent"),
    )
    db.commit()
    return MessageResponse(message="Rating adjusted.")


@router.post("/admin/ratings/recalculate", response_model=MessageResponse)
def recalculate(
    body: RecalculateRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MessageResponse:
    RatingService(db).replay(body.tournament_id)
    db.commit()
    return MessageResponse(message="Ratings recalculated.")
