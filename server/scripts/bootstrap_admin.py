"""
Admin Bootstrap CLI Script for ReconPilot.
Safely provisions an initial administrative user for the demo merchant in development/testing.
Refuses to execute or overwrite if the admin account already exists.
"""

import argparse
import sys
import uuid

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import UserRole, UserStatus
from app.models.merchant import Merchant
from app.models.user import User

DEMO_MERCHANT_ID = uuid.UUID("00000000-0000-4000-a000-000000000001")


def bootstrap_admin(
    email: str = "admin@reconpilot.local",
    password: str = "AdminSecret2026!",
    full_name: str = "ReconPilot Chief Controller",
) -> None:
    settings = get_settings()
    if settings.APP_ENV == "production":
        print("ERROR: bootstrap_admin is disabled in production environments.", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        # 1. Resolve demo merchant
        merchant = db.query(Merchant).filter(Merchant.id == DEMO_MERCHANT_ID).first()
        if not merchant:
            # Fall back to first merchant if demo UUID is not found
            merchant = db.query(Merchant).first()
            if not merchant:
                print(
                    "ERROR: No merchant exists in database. Run database seeder first.",
                    file=sys.stderr,
                )
                sys.exit(1)

        # 2. Check if user already exists
        existing_user = db.query(User).filter(User.email == email.strip().lower()).first()
        if existing_user:
            print(f"INFO: Admin user '{email}' already exists. Skipping bootstrap.")
            return

        # 3. Create admin user
        hashed = hash_password(password)
        admin = User(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            email=email.strip().lower(),
            full_name=full_name,
            password_hash=hashed,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        db.add(admin)

        # Also seed sample operator and reviewer users for testing RBAC
        operator_email = "operator@reconpilot.local"
        if not db.query(User).filter(User.email == operator_email).first():
            operator = User(
                id=uuid.uuid4(),
                merchant_id=merchant.id,
                email=operator_email,
                full_name="Operations Specialist",
                password_hash=hash_password("OperatorSecret2026!"),
                role=UserRole.FINANCE_OPERATOR,
                status=UserStatus.ACTIVE,
            )
            db.add(operator)

        reviewer_email = "reviewer@reconpilot.local"
        if not db.query(User).filter(User.email == reviewer_email).first():
            reviewer = User(
                id=uuid.uuid4(),
                merchant_id=merchant.id,
                email=reviewer_email,
                full_name="Exception Reviewer",
                password_hash=hash_password("ReviewerSecret2026!"),
                role=UserRole.REVIEWER,
                status=UserStatus.ACTIVE,
            )
            db.add(reviewer)

        db.commit()
        print(f"SUCCESS: Bootstrap completed successfully for merchant '{merchant.name}'.")
        print(f" - Admin: {email} (Role: {UserRole.ADMIN.value})")
        print(f" - Operator: {operator_email} (Role: {UserRole.FINANCE_OPERATOR.value})")
        print(f" - Reviewer: {reviewer_email} (Role: {UserRole.REVIEWER.value})")

    except Exception as exc:
        db.rollback()
        print(f"ERROR: Failed to bootstrap admin: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap admin and demo users for ReconPilot")
    parser.add_argument("--email", default="admin@reconpilot.local", help="Admin email")
    parser.add_argument("--password", default="AdminSecret2026!", help="Admin password")
    parser.add_argument("--name", default="ReconPilot Chief Controller", help="Admin full name")
    args = parser.parse_args()

    bootstrap_admin(email=args.email, password=args.password, full_name=args.name)


if __name__ == "__main__":
    main()
