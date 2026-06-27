from sqlalchemy.orm import Session

from app.db.models.player_profile import PlayerProfile
from app.db.models.user import User
from app.schemas.player import ProfileUpdate


class PlayerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_profile(self, *, user: User, data: ProfileUpdate) -> PlayerProfile:
        profile = user.profile
        if data.display_name is not None:
            profile.display_name = data.display_name.strip()
        if data.bio is not None:
            profile.bio = data.bio
        self.db.commit()
        self.db.refresh(profile)
        return profile
