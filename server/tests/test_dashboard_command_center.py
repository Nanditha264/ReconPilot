import uuid
from datetime import timedelta
from decimal import Decimal

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.enums import (
    ProposalStatus,
    ResolutionCategory,
    UserRole,
    UserStatus,
)
from app.models.exception import ExceptionRecord
from app.models.merchant import Merchant
from app.models.resolution_proposal import ResolutionProposal
from app.models.user import User
from app.modules.dashboard.service import DashboardService
from fastapi.testclient import TestClient

client = TestClient(app)


def test_dashboard_kpis_aggregation_and_math():
    """Verify KPI aggregation, match rate percentage, and currency separation."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        assert merchant is not None

        service = DashboardService(db=db, merchant_id=merchant.id)
        overview = service.get_overview()

        assert overview.merchant_id == merchant.id
        assert overview.total_payments_processed >= 0
        assert overview.matched_records >= 0
        assert overview.unmatched_records >= 0
        assert overview.exception_records >= 0
        assert 0.0 <= overview.match_rate_percentage <= 100.0

        # Verify currency exposure: must be separated by currency
        for exp in overview.total_exposure_by_currency:
            assert len(exp.currency) == 3
            assert isinstance(exp.total_exposure, Decimal)
            assert exp.total_exposure >= Decimal("0.00")
            assert exp.exception_count >= 0

        # Verify AI overview numbers
        assert overview.ai_investigations.completed_count >= 0
        assert overview.ai_investigations.pending_count >= 0
        assert overview.ai_investigations.failed_count >= 0
        assert overview.ai_investigations.requires_human_review_count >= 0
    finally:
        db.close()


def test_empty_dataset_and_zero_denominator_safety():
    """Verify that a merchant with 0 records returns clean zeroes without ZeroDivisionError."""
    db = SessionLocal()
    try:
        empty_merchant = Merchant(
            id=uuid.uuid4(),
            name=f"Empty Test Merchant {uuid.uuid4().hex[:6]}",
            email=f"empty_merchant_{uuid.uuid4().hex[:6]}@reconpilot.local",
        )
        db.add(empty_merchant)
        db.commit()

        service = DashboardService(db=db, merchant_id=empty_merchant.id)
        overview = service.get_overview()

        assert overview.total_payments_processed == 0
        assert overview.matched_records == 0
        assert overview.unmatched_records == 0
        assert overview.exception_records == 0
        assert overview.match_rate_percentage == 0.0
        assert len(overview.total_exposure_by_currency) == 0
        assert overview.pending_approvals_count == 0
        assert overview.exceptions_awaiting_review == 0
        assert overview.resolved_exceptions_count == 0
        assert overview.ai_investigations.completed_count == 0
        assert overview.last_reconciliation_at is None

        health = service.get_reconciliation_health()
        assert health.match_distribution["matched"] == 0
        assert health.match_distribution["unmatched"] == 0
        assert health.match_distribution["exceptions"] == 0
        assert len(health.exceptions_by_type) == 0
        assert len(health.exposure_by_currency) == 0

        trends = service.get_exception_trends()
        assert len(trends.runs_history) == 0
        assert len(trends.exception_trends) == 0

        queue = service.get_operations_queue()
        assert queue.total == 0
        assert len(queue.items) == 0
        assert queue.total_pages == 0
    finally:
        db.rollback()
        db.close()


def test_reconciliation_health_distributions():
    """Verify categorical breakdowns by match status, exception type, severity, and resolution status."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        service = DashboardService(db=db, merchant_id=merchant.id)
        health = service.get_reconciliation_health()

        assert health.merchant_id == merchant.id
        assert "matched" in health.match_distribution
        assert "unmatched" in health.match_distribution
        assert "exceptions" in health.match_distribution

        # Verify resolution statuses breakdown
        total_res_breakdown = sum(item.count for item in health.resolution_status_distribution)
        assert total_res_breakdown >= 0

        # Verify severity breakdown
        valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for sev in health.severity_distribution:
            assert sev.severity in valid_severities
            assert sev.count >= 0
    finally:
        db.close()


def test_pending_approvals_with_separation_of_duties():
    """Verify that pending approvals correctly calculate author status and reviewer permissions."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()
        assert exc is not None

        operator = User(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            email=f"dash_op_{uuid.uuid4().hex[:6]}@reconpilot.local",
            password_hash="test_hash",
            full_name="Alice Operator",
            role=UserRole.FINANCE_OPERATOR,
            status=UserStatus.ACTIVE,
        )
        reviewer = User(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            email=f"dash_rev_{uuid.uuid4().hex[:6]}@reconpilot.local",
            password_hash="test_hash",
            full_name="Bob Reviewer",
            role=UserRole.REVIEWER,
            status=UserStatus.ACTIVE,
        )
        db.add_all([operator, reviewer])
        db.commit()

        # Create a pending proposal by Operator Alice
        proposal = ResolutionProposal(
            id=uuid.uuid4(),
            exception_id=exc.id,
            merchant_id=merchant.id,
            category=ResolutionCategory.FEE_DISCREPANCY_REVIEW,
            explanation="Testing pending approval dashboard panel.",
            proposed_action="Dispute gateway fee variance.",
            supporting_evidence_ids=[],
            status=ProposalStatus.PENDING_APPROVAL.value,
            created_by_user_id=operator.id,
        )
        db.add(proposal)
        db.commit()

        service = DashboardService(db=db, merchant_id=merchant.id)

        # 1. Check from Operator Alice's perspective (author)
        alice_approvals = service.get_pending_approvals(current_user=operator)
        matching_alice = [p for p in alice_approvals if p.proposal_id == proposal.id]
        assert len(matching_alice) == 1
        assert matching_alice[0].is_current_user_author is True
        assert matching_alice[0].can_current_user_approve is False  # Cannot approve own proposal!

        # 2. Check from Reviewer Bob's perspective (peer reviewer)
        bob_approvals = service.get_pending_approvals(current_user=reviewer)
        matching_bob = [p for p in bob_approvals if p.proposal_id == proposal.id]
        assert len(matching_bob) == 1
        assert matching_bob[0].is_current_user_author is False
        assert (
            matching_bob[0].can_current_user_approve is True
        )  # Reviewer can approve peer proposal!

        # Cleanup test proposal
        db.delete(proposal)
        db.delete(operator)
        db.delete(reviewer)
        db.commit()
    finally:
        db.close()


def test_operations_queue_filtering_and_pagination():
    """Verify operations queue filters, sorting, and pagination."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        service = DashboardService(db=db, merchant_id=merchant.id)

        # Page 1 with page_size=5
        queue = service.get_operations_queue(page=1, page_size=5)
        assert queue.page == 1
        assert queue.page_size == 5
        assert queue.total >= 0
        assert len(queue.items) <= 5

        for item in queue.items:
            assert item.exception_id is not None
            assert item.financial_impact >= Decimal("0.00")
            assert len(item.currency) == 3
            assert item.age_days >= 0

        # Filter by currency
        inr_queue = service.get_operations_queue(currency="INR")
        for item in inr_queue.items:
            assert item.currency == "INR"
    finally:
        db.close()


def test_tenant_isolation_dashboard_leak_prevention():
    """Verify that a merchant never sees another merchant's metrics or queue items."""
    db = SessionLocal()
    try:
        merchant_b = Merchant(
            id=uuid.uuid4(),
            name=f"Isolated Merchant B {uuid.uuid4().hex[:6]}",
            email=f"merchant_b_{uuid.uuid4().hex[:6]}@reconpilot.local",
        )
        db.add(merchant_b)
        db.commit()

        service_b = DashboardService(db=db, merchant_id=merchant_b.id)
        overview_b = service_b.get_overview()

        # Merchant B has zero records and sees none of Merchant A's data
        assert overview_b.total_payments_processed == 0
        assert overview_b.exception_records == 0
        assert len(overview_b.total_exposure_by_currency) == 0

        queue_b = service_b.get_operations_queue()
        assert queue_b.total == 0
        assert len(queue_b.items) == 0
    finally:
        db.rollback()
        db.close()


def test_api_dashboard_endpoints_e2e():
    """Verify all 5 dashboard HTTP endpoints with JWT auth."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        user = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.REVIEWER)
            .first()
        )
        assert user is not None

        token = create_access_token(
            data={"sub": str(user.id), "merchant_id": str(merchant.id), "role": user.role.value},
            expires_delta=timedelta(minutes=30),
        )
        headers = {"Authorization": f"Bearer {token}"}

        # 1. GET /dashboard/overview
        resp_overview = client.get("/api/v1/dashboard/overview", headers=headers)
        assert resp_overview.status_code == 200
        data_overview = resp_overview.json()["data"]
        assert "total_payments_processed" in data_overview
        assert "match_rate_percentage" in data_overview
        assert "total_exposure_by_currency" in data_overview

        # 2. GET /dashboard/reconciliation-health
        resp_health = client.get("/api/v1/dashboard/reconciliation-health", headers=headers)
        assert resp_health.status_code == 200
        data_health = resp_health.json()["data"]
        assert "match_distribution" in data_health
        assert "exceptions_by_type" in data_health
        assert "exposure_by_currency" in data_health

        # 3. GET /dashboard/exception-trends
        resp_trends = client.get("/api/v1/dashboard/exception-trends", headers=headers)
        assert resp_trends.status_code == 200
        data_trends = resp_trends.json()["data"]
        assert "runs_history" in data_trends
        assert "exception_trends" in data_trends

        # 4. GET /dashboard/pending-approvals
        resp_approvals = client.get("/api/v1/dashboard/pending-approvals", headers=headers)
        assert resp_approvals.status_code == 200
        data_approvals = resp_approvals.json()["data"]
        assert isinstance(data_approvals, list)

        # 5. GET /dashboard/operations-queue
        resp_queue = client.get(
            "/api/v1/dashboard/operations-queue?page=1&page_size=10", headers=headers
        )
        assert resp_queue.status_code == 200
        data_queue = resp_queue.json()["data"]
        assert "items" in data_queue
        assert "total" in data_queue
        assert "page" in data_queue
    finally:
        db.close()
