import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import errors
from app.core.deps import get_current_user
from app.db.models.player_profile import PlayerProfile
from app.db.models.user import User
from app.db.session import get_db
from app.domain import skills as skills_domain
from app.schemas.mappers import to_profile_out
from app.schemas.player import PlayerProfileOut, ProfileUpdate
from app.schemas.skill import PlayerSkillsOut, SkillItem
from app.services.player_service import PlayerService

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{player_id}/skills", response_model=PlayerSkillsOut)
def get_player_skills(player_id: uuid.UUID, db: Session = Depends(get_db)) -> PlayerSkillsOut:
    # Public skill card (per project decision).
    profile = db.get(PlayerProfile, player_id)
    if profile is None:
        raise errors.player_not_found()
    return PlayerSkillsOut(
        player_id=profile.id,
        display_name=profile.display_name,
        skills=[SkillItem(**item) for item in skills_domain.labelled(profile.skill_ratings)],
    )


@router.get("/me", response_model=PlayerProfileOut)
def get_me(user: User = Depends(get_current_user)) -> PlayerProfileOut:
    return to_profile_out(user)


@router.patch("/me", response_model=PlayerProfileOut)
def update_me(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlayerProfileOut:
    PlayerService(db).update_profile(user=user, data=body)
    db.refresh(user)
    return to_profile_out(user)
