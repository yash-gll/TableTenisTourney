import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_request_meta, require_admin, require_approved_player
from app.db.models.enums import RegistrationStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import MessageResponse
from app.schemas.registration import MyRegistrationOut, RegistrationCreate, RegistrationOut
from app.services.registration_service import RegistrationService

router = APIRouter(prefix="/tournaments/{tournament_id}/registrations", tags=["registrations"])


# -- player -----------------------------------------------------------------


@router.post("", response_model=MyRegistrationOut, status_code=status.HTTP_201_CREATED)
def register(
    tournament_id: uuid.UUID,
    body: RegistrationCreate,
    user: User = Depends(require_approved_player),
    db: Session = Depends(get_db),
) -> MyRegistrationOut:
    reg = RegistrationService(db).request(
        tournament_id=tournament_id,
        player_id=user.profile.id,
        preferred_partner_id=body.preferred_partner_id,
        note=body.note,
    )
    return MyRegistrationOut(status=reg.status)


@router.get("/me", response_model=MyRegistrationOut)
def my_registration(
    tournament_id: uuid.UUID,
    user: User = Depends(require_approved_player),
    db: Session = Depends(get_db),
) -> MyRegistrationOut:
    status_ = RegistrationService(db).my_status(tournament_id=tournament_id, player_id=user.profile.id)
    return MyRegistrationOut(status=status_)


@router.delete("/me", response_model=MessageResponse)
def withdraw(
    tournament_id: uuid.UUID,
    user: User = Depends(require_approved_player),
    db: Session = Depends(get_db),
) -> MessageResponse:
    RegistrationService(db).withdraw(tournament_id=tournament_id, player_id=user.profile.id)
    return MessageResponse(message="Registration withdrawn.")


# -- admin ------------------------------------------------------------------


@router.get("", response_model=list[RegistrationOut])
def list_registrations(
    tournament_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[RegistrationOut]:
    rows = RegistrationService(db).list_for_tournament(tournament_id)
    return [
        RegistrationOut(
            player_id=reg.player_id,
            display_name=name,
            status=reg.status,
            preferred_partner_id=reg.preferred_partner_id,
            note=reg.note,
            created_at=reg.created_at,
        )
        for reg, name in rows
    ]


def _admin_set(action_status: RegistrationStatus):
    def handler(
        tournament_id: uuid.UUID,
        player_id: uuid.UUID,
        actor: User = Depends(require_admin),
        db: Session = Depends(get_db),
        meta: dict = Depends(get_request_meta),
    ) -> RegistrationOut:
        reg = RegistrationService(db).set_status(
            tournament_id=tournament_id, player_id=player_id, status=action_status,
            actor=actor, meta=meta,
        )
        return RegistrationOut(
            player_id=reg.player_id, display_name="", status=reg.status,
            preferred_partner_id=reg.preferred_partner_id, note=reg.note, created_at=reg.created_at,
        )

    return handler


router.add_api_route(
    "/{player_id}/accept", _admin_set(RegistrationStatus.ACCEPTED), methods=["POST"],
    response_model=RegistrationOut,
)
router.add_api_route(
    "/{player_id}/decline", _admin_set(RegistrationStatus.DECLINED), methods=["POST"],
    response_model=RegistrationOut,
)
router.add_api_route(
    "/{player_id}/waitlist", _admin_set(RegistrationStatus.WAITLISTED), methods=["POST"],
    response_model=RegistrationOut,
)
