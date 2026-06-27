import uuid

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_token
from app.db.models.enums import AccountStatus, ApprovalStatus, UserRole
from app.db.models.user import User
from app.db.session import get_db

# auto_error=False so we can emit our own error envelope instead of FastAPI's.
_bearer = HTTPBearer(auto_error=False)


def _unauthenticated() -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, "UNAUTHENTICATED", "Authentication required.")


def _forbidden() -> AppError:
    return AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "You do not have access to this resource.")


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise _unauthenticated()
    payload = decode_token(creds.credentials)
    if not payload or payload.get("type") != "access":
        raise _unauthenticated()
    sub = payload.get("sub")
    try:
        user_id = uuid.UUID(str(sub))
    except (ValueError, TypeError):
        raise _unauthenticated() from None
    user = db.get(User, user_id)
    if user is None or user.account_status == AccountStatus.DISABLED:
        raise _unauthenticated()
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise _forbidden()
    return user


def require_approved_player(user: User = Depends(get_current_user)) -> User:
    profile = user.profile
    if profile is None or profile.approval_status != ApprovalStatus.APPROVED:
        raise _forbidden()
    return user


def get_request_meta(request: Request) -> dict[str, str | None]:
    client = request.client
    return {
        "ip_address": client.host if client else None,
        "user_agent": request.headers.get("user-agent"),
    }
