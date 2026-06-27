import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_request_meta, require_admin
from app.db.models.enums import ApprovalStatus
from app.db.models.user import User
from app.db.session import get_db
from app.domain import skills as skills_domain
from app.schemas.admin import AdminPlayerOut, RejectRequest, SuspendRequest
from app.schemas.mappers import to_admin_player_out
from app.schemas.skill import PlayerSkillsOut, SkillItem, SkillsUpdate
from app.services.admin_player_service import AdminPlayerService

router = APIRouter(prefix="/admin/players", tags=["admin"])


@router.patch("/{player_id}/skills", response_model=PlayerSkillsOut)
def update_skills(
    player_id: uuid.UUID,
    body: SkillsUpdate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> PlayerSkillsOut:
    profile = AdminPlayerService(db).update_skills(
        player_id=player_id, ratings=body.ratings, actor=actor, meta=meta
    )
    return PlayerSkillsOut(
        player_id=profile.id,
        display_name=profile.display_name,
        skills=[SkillItem(**item) for item in skills_domain.labelled(profile.skill_ratings)],
    )


@router.get("", response_model=list[AdminPlayerOut])
def list_players(
    approval_status: ApprovalStatus | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminPlayerOut]:
    players = AdminPlayerService(db).list_players(approval_status=approval_status)
    return [to_admin_player_out(p) for p in players]


@router.post("/{player_id}/approve", response_model=AdminPlayerOut)
def approve(
    player_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> AdminPlayerOut:
    profile = AdminPlayerService(db).approve(player_id=player_id, actor=actor, meta=meta)
    return to_admin_player_out(profile)


@router.post("/{player_id}/reject", response_model=AdminPlayerOut)
def reject(
    player_id: uuid.UUID,
    body: RejectRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> AdminPlayerOut:
    profile = AdminPlayerService(db).reject(
        player_id=player_id, actor=actor, reason=body.reason, meta=meta
    )
    return to_admin_player_out(profile)


@router.post("/{player_id}/suspend", response_model=AdminPlayerOut)
def suspend(
    player_id: uuid.UUID,
    body: SuspendRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> AdminPlayerOut:
    profile = AdminPlayerService(db).suspend(
        player_id=player_id, actor=actor, reason=body.reason, meta=meta
    )
    return to_admin_player_out(profile)


@router.post("/{player_id}/restore", response_model=AdminPlayerOut)
def restore(
    player_id: uuid.UUID,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> AdminPlayerOut:
    profile = AdminPlayerService(db).restore(player_id=player_id, actor=actor, meta=meta)
    return to_admin_player_out(profile)
