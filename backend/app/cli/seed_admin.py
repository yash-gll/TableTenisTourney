"""Create (or promote) an administrator account.

Usage:
    python -m app.cli.seed_admin --email admin@example.com --password secret123 \
        --display-name "Site Admin"
"""

import argparse
from datetime import UTC, datetime

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.models.enums import AccountStatus, ApprovalStatus, UserRole
from app.db.models.player_profile import PlayerProfile
from app.db.models.user import User
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed an admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--display-name", default="Administrator")
    args = parser.parse_args()

    email = args.email.strip().lower()
    now = datetime.now(tz=UTC)

    db = SessionLocal()
    try:
        user = db.execute(
            select(User).where(func.lower(User.email) == email)
        ).scalar_one_or_none()

        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(args.password),
                role=UserRole.ADMIN,
                account_status=AccountStatus.ACTIVE,
                email_verified_at=now,
            )
            db.add(user)
            db.flush()
            db.add(
                PlayerProfile(
                    user_id=user.id,
                    display_name=args.display_name,
                    approval_status=ApprovalStatus.APPROVED,
                    approved_at=now,
                )
            )
            print(f"Created admin {email}")
        else:
            user.role = UserRole.ADMIN
            user.account_status = AccountStatus.ACTIVE
            if user.email_verified_at is None:
                user.email_verified_at = now
            print(f"Promoted existing user {email} to admin")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
