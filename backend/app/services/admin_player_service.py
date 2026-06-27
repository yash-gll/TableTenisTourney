import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import (
    AccountStatus,
    ApprovalStatus,
    AuditSeverity,
)
from app.db.models.player_profile import PlayerProfile
from app.db.models.user import User
from app.domain import skills as skills_domain
from app.services.audit_service import AuditService


def _now() -> datetime:
    return datetime.now(tz=UTC)


class AdminPlayerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def list_players(self, *, approval_status: ApprovalStatus | None) -> list[PlayerProfile]:
        stmt = select(PlayerProfile)
        if approval_status is not None:
            stmt = stmt.where(PlayerProfile.approval_status == approval_status)
        stmt = stmt.order_by(PlayerProfile.created_at.asc())
        return list(self.db.execute(stmt).scalars())

    def _get_profile(self, player_id: uuid.UUID) -> PlayerProfile:
        profile = self.db.get(PlayerProfile, player_id)
        if profile is None:
            raise errors.player_not_found()
        return profile

    def _transition(
        self,
        *,
        player_id: uuid.UUID,
        actor: User,
        new_status: ApprovalStatus,
        action: str,
        reason: str | None,
        new_account_status: AccountStatus | None,
        severity: AuditSeverity,
        meta: dict,
    ) -> PlayerProfile:
        profile = self._get_profile(player_id)
        before = {
            "approval_status": profile.approval_status.value,
            "approval_reason": profile.approval_reason,
        }

        profile.approval_status = new_status
        profile.approval_reason = reason
        if new_status == ApprovalStatus.APPROVED:
            profile.approved_by = actor.id
            profile.approved_at = _now()
            # Seed a baseline skill set on first approval (don't overwrite if set).
            if not profile.skill_ratings:
                profile.skill_ratings = skills_domain.default_ratings()

        if new_account_status is not None or new_status == ApprovalStatus.APPROVED:
            user = self.db.get(User, profile.user_id)
            if user is not None:
                if new_account_status is not None:
                    user.account_status = new_account_status
                # Approving (or restoring) also verifies the email so the player
                # can log in — useful when there's no email service.
                if new_status == ApprovalStatus.APPROVED and user.email_verified_at is None:
                    user.email_verified_at = _now()

        self.audit.record(
            actor_user_id=actor.id,
            action=action,
            entity_type="player_profile",
            entity_id=str(profile.id),
            before_data=before,
            after_data={
                "approval_status": profile.approval_status.value,
                "approval_reason": profile.approval_reason,
            },
            reason=reason,
            severity=severity,
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_skills(
        self, *, player_id: uuid.UUID, ratings: dict[str, int], actor: User, meta: dict
    ) -> PlayerProfile:
        ok, message = skills_domain.validate_ratings(ratings)
        if not ok:
            raise errors.invalid_skill_rating(message or "Invalid skill ratings.")
        profile = self._get_profile(player_id)
        merged = dict(profile.skill_ratings or {})
        merged.update(ratings)
        profile.skill_ratings = merged
        self.audit.record(
            actor_user_id=actor.id,
            action="player.update_skills",
            entity_type="player_profile",
            entity_id=str(profile.id),
            after_data={"skill_ratings": merged},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def approve(self, *, player_id: uuid.UUID, actor: User, meta: dict) -> PlayerProfile:
        return self._transition(
            player_id=player_id,
            actor=actor,
            new_status=ApprovalStatus.APPROVED,
            action="player.approve",
            reason=None,
            new_account_status=AccountStatus.ACTIVE,
            severity=AuditSeverity.INFO,
            meta=meta,
        )

    def reject(self, *, player_id: uuid.UUID, actor: User, reason: str, meta: dict) -> PlayerProfile:
        if not reason.strip():
            raise errors.reason_required()
        return self._transition(
            player_id=player_id,
            actor=actor,
            new_status=ApprovalStatus.REJECTED,
            action="player.reject",
            reason=reason,
            new_account_status=None,
            severity=AuditSeverity.WARNING,
            meta=meta,
        )

    def suspend(self, *, player_id: uuid.UUID, actor: User, reason: str, meta: dict) -> PlayerProfile:
        if not reason.strip():
            raise errors.reason_required()
        return self._transition(
            player_id=player_id,
            actor=actor,
            new_status=ApprovalStatus.SUSPENDED,
            action="player.suspend",
            reason=reason,
            new_account_status=AccountStatus.SUSPENDED,
            severity=AuditSeverity.WARNING,
            meta=meta,
        )

    def restore(self, *, player_id: uuid.UUID, actor: User, meta: dict) -> PlayerProfile:
        return self._transition(
            player_id=player_id,
            actor=actor,
            new_status=ApprovalStatus.APPROVED,
            action="player.restore",
            reason=None,
            new_account_status=AccountStatus.ACTIVE,
            severity=AuditSeverity.INFO,
            meta=meta,
        )
