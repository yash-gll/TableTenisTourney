import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import errors
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models.auth_token import AuthToken, RefreshToken
from app.db.models.enums import AccountStatus, ApprovalStatus, AuthTokenType, UserRole
from app.db.models.player_profile import PlayerProfile
from app.db.models.user import User
from app.schemas.auth import TokenPair

logger = logging.getLogger("app.auth")


def _now() -> datetime:
    return datetime.now(tz=UTC)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- lookups -----------------------------------------------------------

    def _get_user_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        return self.db.execute(
            select(User).where(func.lower(User.email) == normalized)
        ).scalar_one_or_none()

    # -- registration / verification --------------------------------------

    def register(self, *, email: str, password: str, display_name: str) -> User:
        normalized = email.strip().lower()
        if self._get_user_by_email(normalized) is not None:
            raise errors.email_already_registered()

        user = User(
            email=normalized,
            password_hash=hash_password(password),
            role=UserRole.PLAYER,
            account_status=AccountStatus.ACTIVE,
        )
        self.db.add(user)
        self.db.flush()  # assign user.id

        profile = PlayerProfile(
            user_id=user.id,
            display_name=display_name.strip(),
            approval_status=ApprovalStatus.PENDING,
        )
        self.db.add(profile)

        self._issue_verification(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _issue_verification(self, user: User) -> None:
        raw = generate_opaque_token()
        token = AuthToken(
            user_id=user.id,
            token_type=AuthTokenType.EMAIL_VERIFY,
            token_hash=hash_token(raw),
            expires_at=_now() + timedelta(hours=settings.verify_token_ttl_hours),
        )
        self.db.add(token)
        link = f"{settings.frontend_url}/verify-email?token={raw}"
        # No email infra (personal project): surface the link via logs.
        logger.info("EMAIL VERIFICATION for %s: %s", user.email, link)

    def resend_verification(self, *, email: str) -> None:
        user = self._get_user_by_email(email)
        # Do not reveal whether the email exists.
        if user is not None and not user.is_verified:
            self._issue_verification(user)
            self.db.commit()

    def verify_email(self, *, token: str) -> None:
        record = self._consume_token(token, AuthTokenType.EMAIL_VERIFY)
        user = self.db.get(User, record.user_id)
        if user is None:
            raise errors.invalid_token()
        if user.email_verified_at is None:
            user.email_verified_at = _now()
        self.db.commit()

    def _consume_token(self, raw: str, token_type: AuthTokenType) -> AuthToken:
        record = self.db.execute(
            select(AuthToken).where(
                AuthToken.token_hash == hash_token(raw),
                AuthToken.token_type == token_type,
            )
        ).scalar_one_or_none()
        if record is None or record.used_at is not None:
            raise errors.invalid_token()
        expires = record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < _now():
            raise errors.invalid_token("Token has expired.")
        record.used_at = _now()
        return record

    # -- login / sessions --------------------------------------------------

    def login(self, *, email: str, password: str) -> tuple[User, TokenPair]:
        user = self._get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise errors.invalid_credentials()
        if not user.is_verified:
            raise errors.email_not_verified()
        if user.account_status != AccountStatus.ACTIVE:
            raise errors.account_not_active()

        user.last_login_at = _now()
        tokens = self._issue_token_pair(user)
        self.db.commit()
        return user, tokens

    def _issue_token_pair(self, user: User) -> TokenPair:
        access = create_access_token(user_id=str(user.id), role=user.role.value)
        refresh, jti, expires_at = create_refresh_token(user_id=str(user.id))
        self.db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
        return TokenPair(access_token=access, refresh_token=refresh)

    def refresh(self, *, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise errors.invalid_token("Invalid refresh token.")
        jti = payload.get("jti")
        record = self.db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        ).scalar_one_or_none()
        if record is None or record.revoked_at is not None:
            raise errors.invalid_token("Refresh token is not valid.")

        user = self.db.get(User, record.user_id)
        if user is None or user.account_status == AccountStatus.DISABLED:
            raise errors.invalid_token("Refresh token is not valid.")

        # Rotate: revoke the old jti, issue a fresh pair.
        record.revoked_at = _now()
        tokens = self._issue_token_pair(user)
        self.db.commit()
        return tokens

    def logout(self, *, refresh_token: str) -> None:
        payload = decode_token(refresh_token)
        if not payload:
            return
        jti = payload.get("jti")
        record = self.db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        ).scalar_one_or_none()
        if record is not None and record.revoked_at is None:
            record.revoked_at = _now()
            self.db.commit()

    # -- password reset ----------------------------------------------------

    def forgot_password(self, *, email: str) -> None:
        user = self._get_user_by_email(email)
        if user is None:
            return  # do not reveal existence
        raw = generate_opaque_token()
        token = AuthToken(
            user_id=user.id,
            token_type=AuthTokenType.PASSWORD_RESET,
            token_hash=hash_token(raw),
            expires_at=_now() + timedelta(hours=settings.reset_token_ttl_hours),
        )
        self.db.add(token)
        link = f"{settings.frontend_url}/reset-password?token={raw}"
        logger.info("PASSWORD RESET for %s: %s", user.email, link)
        self.db.commit()

    def reset_password(self, *, token: str, password: str) -> None:
        record = self._consume_token(token, AuthTokenType.PASSWORD_RESET)
        user = self.db.get(User, record.user_id)
        if user is None:
            raise errors.invalid_token()
        user.password_hash = hash_password(password)
        # Revoke all active refresh tokens on password change.
        for rt in self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
            )
        ).scalars():
            rt.revoked_at = _now()
        self.db.commit()
