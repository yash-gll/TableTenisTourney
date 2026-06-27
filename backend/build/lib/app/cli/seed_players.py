"""Seed approved test players for shaking out the app locally.

Creates verified + APPROVED players so an admin can immediately build teams.
Idempotent: existing emails are skipped.

Usage:
    python -m app.cli.seed_players --count 10 --password 'PlayerPass1'
"""

import argparse
from datetime import UTC, datetime

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.models.enums import AccountStatus, ApprovalStatus, UserRole
from app.db.models.player_profile import PlayerProfile
from app.db.models.user import User
from app.db.session import SessionLocal

NAMES = [
    "Alice Ace", "Bob Smash", "Cara Chop", "Dan Drive", "Eve Edge",
    "Finn Flick", "Gina Grip", "Hugo Hook", "Iris Inswing", "Jack Joker",
    "Kira Knock", "Leo Loop", "Mia Mash", "Noah Net", "Opal Offsie",
    "Pia Pivot", "Quinn Quick", "Ravi Rally", "Sara Spin", "Tom Topspin",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed approved test players.")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--password", default="PlayerPass1")
    args = parser.parse_args()

    now = datetime.now(tz=UTC)
    created = 0
    db = SessionLocal()
    try:
        for i in range(args.count):
            name = NAMES[i % len(NAMES)]
            suffix = i // len(NAMES)
            display = name if suffix == 0 else f"{name} {suffix + 1}"
            email = f"player{i + 1}@example.com"

            exists = db.execute(
                select(User).where(func.lower(User.email) == email)
            ).scalar_one_or_none()
            if exists is not None:
                continue

            user = User(
                email=email,
                password_hash=hash_password(args.password),
                role=UserRole.PLAYER,
                account_status=AccountStatus.ACTIVE,
                email_verified_at=now,
            )
            db.add(user)
            db.flush()
            db.add(
                PlayerProfile(
                    user_id=user.id,
                    display_name=display,
                    approval_status=ApprovalStatus.APPROVED,
                    approved_at=now,
                )
            )
            created += 1

        db.commit()
        print(f"Created {created} approved players (password: {args.password}).")
        print(f"Emails: player1@example.com … player{args.count}@example.com")
    finally:
        db.close()


if __name__ == "__main__":
    main()
