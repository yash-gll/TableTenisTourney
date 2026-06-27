import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.domain import skills as skills_domain
from app.schemas.mappers import to_profile_out
from app.schemas.player import (
    BadgeOut,
    PlayerAchievementsOut,
    PlayerProfileOut,
    PlayerRivalsOut,
    ProfileUpdate,
    PublicPlayerOut,
    PublicProfileOut,
    RivalOut,
)
from app.schemas.skill import PlayerSkillsOut, SkillItem
from app.services.player_service import PlayerService

router = APIRouter(prefix="/players", tags=["players"])


# Literal routes are declared before the {player_id} routes so "me" isn't
# captured as a path param.


@router.get("", response_model=list[PublicPlayerOut])
def search_players(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[PublicPlayerOut]:
    players = PlayerService(db).search(query=search)
    return [
        PublicPlayerOut(
            player_id=p.id,
            display_name=p.display_name,
            current_rating=p.current_rating,
            highest_rating=p.highest_rating,
        )
        for p in players
    ]


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


@router.get("/{player_id}", response_model=PublicProfileOut)
def get_public_profile(player_id: uuid.UUID, db: Session = Depends(get_db)) -> PublicProfileOut:
    service = PlayerService(db)
    profile = service.get_profile(player_id)
    return PublicProfileOut(
        player_id=profile.id,
        display_name=profile.display_name,
        current_rating=profile.current_rating,
        highest_rating=profile.highest_rating,
        stats=service.stats(player_id),
        recent_form=service.recent_form(player_id),
    )


@router.get("/{player_id}/rivals", response_model=PlayerRivalsOut)
def get_player_rivals(player_id: uuid.UUID, db: Session = Depends(get_db)) -> PlayerRivalsOut:
    service = PlayerService(db)
    service.get_profile(player_id)
    return PlayerRivalsOut(
        player_id=player_id,
        rivals=[RivalOut(**r) for r in service.rivals(player_id)],
    )


@router.get("/{player_id}/achievements", response_model=PlayerAchievementsOut)
def get_player_achievements(
    player_id: uuid.UUID, db: Session = Depends(get_db)
) -> PlayerAchievementsOut:
    service = PlayerService(db)
    service.get_profile(player_id)  # 404 if unknown
    badges = service.achievements(player_id)
    return PlayerAchievementsOut(
        player_id=player_id,
        achievements=[
            BadgeOut(key=b.key, label=b.label, icon=b.icon, description=b.description)
            for b in badges
        ],
    )


@router.get("/{player_id}/skills", response_model=PlayerSkillsOut)
def get_player_skills(player_id: uuid.UUID, db: Session = Depends(get_db)) -> PlayerSkillsOut:
    profile = PlayerService(db).get_profile(player_id)
    return PlayerSkillsOut(
        player_id=profile.id,
        display_name=profile.display_name,
        skills=[SkillItem(**item) for item in skills_domain.labelled(profile.skill_ratings)],
    )
