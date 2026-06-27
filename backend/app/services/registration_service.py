import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import RegistrationStatus, TournamentStatus
from app.db.models.player_profile import PlayerProfile
from app.db.models.tournament import Tournament
from app.db.models.tournament_registration import TournamentRegistration
from app.db.models.user import User
from app.services.audit_service import AuditService

# Admin-settable statuses via the accept/decline/waitlist endpoints.
ADMIN_SETTABLE = {
    RegistrationStatus.ACCEPTED,
    RegistrationStatus.DECLINED,
    RegistrationStatus.WAITLISTED,
}


class RegistrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def _tournament(self, tournament_id: uuid.UUID) -> Tournament:
        t = self.db.get(Tournament, tournament_id)
        if t is None:
            raise errors.tournament_not_found()
        return t

    def _get(self, tournament_id: uuid.UUID, player_id: uuid.UUID) -> TournamentRegistration | None:
        return self.db.execute(
            select(TournamentRegistration).where(
                TournamentRegistration.tournament_id == tournament_id,
                TournamentRegistration.player_id == player_id,
            )
        ).scalar_one_or_none()

    # -- player actions ----------------------------------------------------

    def request(
        self, *, tournament_id: uuid.UUID, player_id: uuid.UUID,
        preferred_partner_id: uuid.UUID | None, note: str | None,
    ) -> TournamentRegistration:
        tournament = self._tournament(tournament_id)
        if tournament.status != TournamentStatus.REGISTRATION_OPEN:
            raise errors.registration_not_open()

        existing = self._get(tournament_id, player_id)
        if existing is not None:
            # Re-requesting after withdrawing/declining is allowed.
            if existing.status in (RegistrationStatus.WITHDRAWN, RegistrationStatus.DECLINED):
                existing.status = RegistrationStatus.REQUESTED
                existing.preferred_partner_id = preferred_partner_id
                existing.note = note
                self.db.commit()
                self.db.refresh(existing)
                return existing
            raise errors.already_registered()

        reg = TournamentRegistration(
            tournament_id=tournament_id,
            player_id=player_id,
            status=RegistrationStatus.REQUESTED,
            preferred_partner_id=preferred_partner_id,
            note=note,
        )
        self.db.add(reg)
        self.db.commit()
        self.db.refresh(reg)
        return reg

    def withdraw(self, *, tournament_id: uuid.UUID, player_id: uuid.UUID) -> None:
        reg = self._get(tournament_id, player_id)
        if reg is None:
            raise errors.registration_not_found()
        reg.status = RegistrationStatus.WITHDRAWN
        self.db.commit()

    def my_status(
        self, *, tournament_id: uuid.UUID, player_id: uuid.UUID
    ) -> RegistrationStatus | None:
        reg = self._get(tournament_id, player_id)
        return reg.status if reg else None

    # -- admin actions -----------------------------------------------------

    def list_for_tournament(self, tournament_id: uuid.UUID) -> list[tuple[TournamentRegistration, str]]:
        rows = self.db.execute(
            select(TournamentRegistration, PlayerProfile.display_name)
            .join(PlayerProfile, PlayerProfile.id == TournamentRegistration.player_id)
            .where(TournamentRegistration.tournament_id == tournament_id)
            .order_by(TournamentRegistration.created_at)
        ).all()
        return [(reg, name) for reg, name in rows]

    def set_status(
        self, *, tournament_id: uuid.UUID, player_id: uuid.UUID, status: RegistrationStatus,
        actor: User, meta: dict,
    ) -> TournamentRegistration:
        reg = self._get(tournament_id, player_id)
        if reg is None:
            raise errors.registration_not_found()
        before = reg.status.value
        reg.status = status
        self.audit.record(
            actor_user_id=actor.id,
            action=f"registration.{status.value.lower()}",
            entity_type="tournament_registration",
            entity_id=str(reg.id),
            before_data={"status": before},
            after_data={"status": status.value},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(reg)
        return reg
