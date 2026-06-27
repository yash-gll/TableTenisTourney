import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


# Opaque tokens (email verification / password reset) ------------------------


def generate_opaque_token() -> str:
    """Return a URL-safe random token (the raw value handed to the user)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Deterministic hash stored in the DB; raw token is never persisted."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# JWTs -----------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(tz=UTC)


def create_access_token(*, user_id: str, role: str) -> str:
    expire = _now() + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": _now(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, user_id: str) -> tuple[str, str, datetime]:
    """Return (token, jti, expires_at)."""
    jti = str(uuid.uuid4())
    expire = _now() + timedelta(days=settings.refresh_token_ttl_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": jti,
        "exp": expire,
        "iat": _now(),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
