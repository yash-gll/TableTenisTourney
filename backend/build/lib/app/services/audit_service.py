import uuid

from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.enums import AuditSeverity


class AuditService:
    """Captures privileged changes. Adds the row to the caller's session/transaction
    (does not commit) so audit writes are atomic with the action they describe."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        before_data: dict | None = None,
        after_data: dict | None = None,
        reason: str | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_data=before_data,
            after_data=after_data,
            reason=reason,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(entry)
        return entry
