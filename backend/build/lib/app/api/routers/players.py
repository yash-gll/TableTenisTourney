from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.mappers import to_profile_out
from app.schemas.player import PlayerProfileOut, ProfileUpdate
from app.services.player_service import PlayerService

router = APIRouter(prefix="/players", tags=["players"])


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
