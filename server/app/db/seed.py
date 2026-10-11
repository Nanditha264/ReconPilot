"""
ReconPilot Seeder & Database CLI.
Supports:
- Idempotent insert of deterministic dataset (safe to run repeatedly)
- Protected clean reset (--reset --confirm-destructive)
- Production environment safeguards
"""

import argparse
import sys
from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.seed_data import generate_deterministic_dataset
from app.db.session import SessionLocal, check_db_connection
from app.models import (
    Adjustment,
    AIInvestigation,
    AuditEvent,
    BenchmarkCase,
    Evidence,
    ExceptionRecord,
    Fee,
    Merchant,
    Payment,
    ReconciliationResult,
    ReconciliationRun,
    Refund,
    Review,
    Settlement,
    SettlementItem,
    SourceIntegration,
    User,
)


def seed_database(session: Session, verbose: bool = True) -> dict[str, int]:
    """
    Idempotently seeds the database using the deterministic dataset generator.
    If records already exist, they are preserved rather than duplicated.
    """
    dataset = generate_deterministic_dataset()
    counts: dict[str, int] = {}

    # 1. Merchant
    merchant = session.get(Merchant, dataset.merchant["id"])
    if not merchant:
        merchant = Merchant(**dataset.merchant)
        session.add(merchant)
        session.flush()
        counts["merchants"] = 1
    else:
        counts["merchants"] = 0

    # 2. Source Integrations
    counts["source_integrations"] = 0
    for si_data in dataset.source_integrations:
        if not session.get(SourceIntegration, si_data["id"]):
            session.add(SourceIntegration(**si_data))
            counts["source_integrations"] += 1
    session.flush()

    # 3. Payments
    counts["payments"] = 0
    for p_data in dataset.payments:
        if not session.get(Payment, p_data["id"]):
            session.add(Payment(**p_data))
            counts["payments"] += 1
    session.flush()

    # 4. Refunds
    counts["refunds"] = 0
    for r_data in dataset.refunds:
        if not session.get(Refund, r_data["id"]):
            session.add(Refund(**r_data))
            counts["refunds"] += 1
    session.flush()

    # 5. Fees
    counts["fees"] = 0
    for f_data in dataset.fees:
        if not session.get(Fee, f_data["id"]):
            session.add(Fee(**f_data))
            counts["fees"] += 1
    session.flush()

    # 6. Settlements
    counts["settlements"] = 0
    for s_data in dataset.settlements:
        if not session.get(Settlement, s_data["id"]):
            session.add(Settlement(**s_data))
            counts["settlements"] += 1
    session.flush()

    # 7. Settlement Items
    counts["settlement_items"] = 0
    for si_data in dataset.settlement_items:
        if not session.get(SettlementItem, si_data["id"]):
            session.add(SettlementItem(**si_data))
            counts["settlement_items"] += 1
    session.flush()

    # 8. Adjustments
    counts["adjustments"] = 0
    for a_data in dataset.adjustments:
        if not session.get(Adjustment, a_data["id"]):
            session.add(Adjustment(**a_data))
            counts["adjustments"] += 1
    session.flush()

    # 9. Reconciliation Runs
    counts["reconciliation_runs"] = 0
    for run_data in dataset.reconciliation_runs:
        if not session.get(ReconciliationRun, run_data["id"]):
            session.add(ReconciliationRun(**run_data))
            counts["reconciliation_runs"] += 1
    session.flush()

    # 10. Reconciliation Results
    counts["reconciliation_results"] = 0
    for res_data in dataset.reconciliation_results:
        if not session.get(ReconciliationResult, res_data["id"]):
            session.add(ReconciliationResult(**res_data))
            counts["reconciliation_results"] += 1
    session.flush()

    # 11. Exceptions
    counts["exceptions"] = 0
    for exc_data in dataset.exceptions:
        if not session.get(ExceptionRecord, exc_data["id"]):
            session.add(ExceptionRecord(**exc_data))
            counts["exceptions"] += 1
    session.flush()

    # 12. Evidence
    counts["evidence"] = 0
    for ev_data in dataset.evidence_items:
        if not session.get(Evidence, ev_data["id"]):
            session.add(Evidence(**ev_data))
            counts["evidence"] += 1
    session.flush()

    # 13. AI Investigations
    counts["ai_investigations"] = 0
    for ai_data in dataset.ai_investigations:
        if not session.get(AIInvestigation, ai_data["id"]):
            session.add(AIInvestigation(**ai_data))
            counts["ai_investigations"] += 1
    session.flush()

    # 14. Reviews
    counts["reviews"] = 0
    for rev_data in dataset.reviews:
        if not session.get(Review, rev_data["id"]):
            session.add(Review(**rev_data))
            counts["reviews"] += 1
    session.flush()

    # 15. Audit Events
    counts["audit_events"] = 0
    for aud_data in dataset.audit_events:
        if not session.get(AuditEvent, aud_data["id"]):
            session.add(AuditEvent(**aud_data))
            counts["audit_events"] += 1
    session.flush()

    # 16. Benchmark Cases
    counts["benchmark_cases"] = 0
    for bm_data in dataset.benchmark_cases:
        # Check by scenario_id
        existing = session.execute(
            select(BenchmarkCase).where(BenchmarkCase.scenario_id == bm_data["scenario_id"])
        ).scalar_one_or_none()
        if not existing:
            session.add(BenchmarkCase(**bm_data))
            counts["benchmark_cases"] += 1
    session.flush()

    # 17. Default Users (Admin, Operator, Reviewer)
    from app.core.security import hash_password
    from app.models.enums import UserRole, UserStatus

    default_users = [
        {
            "email": "admin@reconpilot.local",
            "password": "AdminSecret2026!",
            "full_name": "ReconPilot Chief Controller",
            "role": UserRole.ADMIN,
        },
        {
            "email": "operator@reconpilot.local",
            "password": "OperatorSecret2026!",
            "full_name": "Operations Specialist",
            "role": UserRole.FINANCE_OPERATOR,
        },
        {
            "email": "reviewer@reconpilot.local",
            "password": "ReviewerSecret2026!",
            "full_name": "Exception Reviewer",
            "role": UserRole.REVIEWER,
        },
    ]

    for u_info in default_users:
        if not session.execute(
            select(User).where(User.email == u_info["email"])
        ).scalar_one_or_none():
            session.add(
                User(
                    merchant_id=merchant.id,
                    email=u_info["email"],
                    full_name=u_info["full_name"],
                    password_hash=hash_password(u_info["password"]),
                    role=u_info["role"],
                    status=UserStatus.ACTIVE,
                )
            )
    session.flush()

    session.commit()

    if verbose:
        print("Seeding completed successfully:")
        for table, count in counts.items():
            print(f"  + {table}: {count} records inserted")

    return counts


def reset_database(session: Session, confirm: bool = False) -> None:
    """
    Safely resets development data. Strictly refuses to run in production.
    Requires explicit confirmation flag.
    """
    settings = get_settings()
    if settings.APP_ENV.lower() in ("production", "prod"):
        raise RuntimeError(
            "FATAL: Resetting the database in a PRODUCTION environment is strictly forbidden."
        )

    if not confirm:
        raise ValueError(
            "Confirmation flag '--confirm-destructive' is required to execute database reset."
        )

    # Delete in reverse foreign key order
    models_to_clear: Sequence[type[Any]] = [
        Review,
        Evidence,
        AIInvestigation,
        AuditEvent,
        ExceptionRecord,
        ReconciliationResult,
        ReconciliationRun,
        SettlementItem,
        Settlement,
        Fee,
        Refund,
        Adjustment,
        Payment,
        SourceIntegration,
        User,
        Merchant,
        BenchmarkCase,
    ]

    for model in models_to_clear:
        session.execute(delete(model))

    session.commit()
    print("Database demo tables safely cleared.")


def main() -> None:
    parser = argparse.ArgumentParser(description="ReconPilot Database Seeder and Management CLI")
    parser.add_argument("--reset", action="store_true", help="Clear all financial demo data")
    parser.add_argument(
        "--confirm-destructive",
        action="store_true",
        help="Explicit confirmation required to reset demo tables",
    )
    args = parser.parse_args()

    connected, msg = check_db_connection()
    if not connected:
        print(f"Error: Unable to connect to PostgreSQL database: {msg}", file=sys.stderr)
        print("Please ensure PostgreSQL service is running and accessible.", file=sys.stderr)
        sys.exit(1)

    session = SessionLocal()
    try:
        if args.reset:
            reset_database(session, confirm=args.confirm_destructive)
        seed_database(session)
    except Exception as exc:
        session.rollback()
        print(f"Failed to execute database operation: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
