"""Helpers that build response schemas from joined User + PlayerProfile models."""

from app.db.models.player_profile import PlayerProfile
from app.db.models.user import User
from app.schemas.admin import AdminPlayerOut
from app.schemas.player import MeResponse, PlayerProfileOut


def to_me(user: User) -> MeResponse:
    profile = user.profile
    return MeResponse(
        user_id=user.id,
        email=user.email,
        role=user.role,
        account_status=user.account_status,
        email_verified=user.is_verified,
        approval_status=profile.approval_status,
        display_name=profile.display_name,
    )


def to_profile_out(user: User) -> PlayerProfileOut:
    profile = user.profile
    return PlayerProfileOut(
        id=profile.id,
        user_id=user.id,
        display_name=profile.display_name,
        email=user.email,
        role=user.role,
        account_status=user.account_status,
        approval_status=profile.approval_status,
        approval_reason=profile.approval_reason,
        current_rating=profile.current_rating,
        highest_rating=profile.highest_rating,
        bio=profile.bio,
        email_verified=user.is_verified,
        created_at=user.created_at,
    )


def to_admin_player_out(profile: PlayerProfile) -> AdminPlayerOut:
    user = profile.user
    return AdminPlayerOut(
        player_id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        email=user.email,
        approval_status=profile.approval_status,
        approval_reason=profile.approval_reason,
        email_verified=user.is_verified,
        created_at=profile.created_at,
    )
