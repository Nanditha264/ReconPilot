import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.adjustment import Adjustment
from app.models.enums import (
    AdjustmentStatus,
    AdjustmentType,
    EvidenceCategory,
    EvidenceStrength,
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    FeeStatus,
    FeeType,
    MatchStatus,
    MatchType,
    PaymentStatus,
    RefundStatus,
    SettlementStatus,
    UserRole,
)
from app.models.exception import ExceptionRecord
from app.models.fee import Fee
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.reconciliation_result import ReconciliationResult
from app.models.reconciliation_run import ReconciliationRun
from app.models.refund import Refund
from app.models.settlement import Settlement
from app.models.settlement_item import SettlementItem
from app.models.user import User
from app.modules.evidence.service import EvidenceCollector, EvidenceCorrelator
from fastapi.testclient import TestClient

client = TestClient(app)
NOW = datetime.now(UTC)


def test_evidence_collector_and_correlator_complete_records():
    """Verify evidence correlation when payment, settlement, fee, refund and adjustments exist."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        assert merchant is not None

        # Create isolated test fixtures
        run = ReconciliationRun(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            run_type="MANUAL_TRIGGER",
            status="COMPLETED",
            started_at=NOW,
            completed_at=NOW,
            total_records=2,
            matched_records=1,
            unmatched_records=0,
            exception_records=1,
        )
        db.add(run)
        db.flush()

        p = Payment(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            external_id=f"pay_ev_test_{uuid.uuid4().hex[:6]}",
            amount=Decimal("5000.00"),
            currency="INR",
            status=PaymentStatus.CAPTURED,
            payment_method="card",
            captured_at=NOW,
            source_created_at=NOW,
        )
        db.add(p)
        db.flush()

        s = Settlement(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            external_id=f"setl_ev_test_{uuid.uuid4().hex[:6]}",
            settlement_date=NOW.date(),
            amount=Decimal("4300.00"),
            currency="INR",
            status=SettlementStatus.SETTLED,
            source_created_at=NOW,
        )
        db.add(s)
        db.flush()

        si = SettlementItem(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            settlement_id=s.id,
            payment_id=p.id,
            external_payment_id=p.external_id,
            gross_amount=Decimal("5000.00"),
            fee_amount=Decimal("200.00"),
            refund_amount=Decimal("500.00"),
            adjustment_amount=Decimal("0.00"),
            net_amount=Decimal("4300.00"),
            currency="INR",
            source_created_at=NOW,
        )
        db.add(si)

        r = Refund(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            payment_id=p.id,
            external_id=f"rfnd_ev_test_{uuid.uuid4().hex[:6]}",
            amount=Decimal("500.00"),
            currency="INR",
            status=RefundStatus.PROCESSED,
            processed_at=NOW,
        )
        db.add(r)

        f = Fee(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            payment_id=p.id,
            fee_type=FeeType.MDR,
            amount=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            currency="INR",
            status=FeeStatus.ASSESSED,
        )
        db.add(f)

        adj = Adjustment(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            payment_id=p.id,
            external_id=f"adj_ev_test_{uuid.uuid4().hex[:6]}",
            amount=Decimal("-50.00"),
            currency="INR",
            adjustment_type=AdjustmentType.PENALTY,
            reason="Service penalty",
            status=AdjustmentStatus.APPLIED,
            effective_at=NOW,
        )
        db.add(adj)

        # Expected: 5000 - 500 - 118 - 50 = 4332. Actual: 4300. Variance: 32
        res = ReconciliationResult(
            id=uuid.uuid4(),
            run_id=run.id,
            merchant_id=merchant.id,
            payment_id=p.id,
            settlement_id=s.id,
            match_type=MatchType.EXACT_2_WAY,
            match_status=MatchStatus.EXCEPTION,
            expected_amount=Decimal("4332.00"),
            actual_amount=Decimal("4300.00"),
            difference=Decimal("32.00"),
            tolerance=Decimal("1.00"),
            confidence=Decimal("1.0000"),
            explanation="Amount variance exceeding tolerance",
            matching_fields={"settlement_item_id": str(si.id)},
        )
        db.add(res)
        db.flush()

        exc = ExceptionRecord(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            reconciliation_result_id=res.id,
            exception_type=ExceptionType.AMOUNT_MISMATCH,
            severity=ExceptionSeverity.MEDIUM,
            status=ExceptionStatus.OPEN,
            financial_impact=Decimal("32.00"),
            currency="INR",
            description="Recorded settlement amount differs by 32.00 INR",
        )
        db.add(exc)
        db.flush()

        # Collect & correlate
        collector = EvidenceCollector(db=db, merchant_id=merchant.id)
        raw = collector.collect(exception_id=exc.id)
        assert raw is not None
        assert raw.payment is not None
        assert raw.settlement_item is not None
        assert len(raw.refunds) == 1
        assert len(raw.fees) == 1
        assert len(raw.adjustments) == 1

        evidence_resp = EvidenceCorrelator.correlate(raw)
        assert evidence_resp.exception_id == exc.id
        assert evidence_resp.reconciliation.expected_amount == Decimal("4332.00")
        assert evidence_resp.reconciliation.actual_amount == Decimal("4300.00")
        assert evidence_resp.reconciliation.variance == Decimal("32.00")
        assert evidence_resp.summary.overall_strength in (
            EvidenceStrength.CONFIRMED,
            EvidenceStrength.CORROBORATED,
        )
        assert evidence_resp.summary.cause_established is True

        categories = {item.category for item in evidence_resp.evidence_items}
        assert EvidenceCategory.PAYMENT in categories
        assert EvidenceCategory.SETTLEMENT in categories
        assert EvidenceCategory.REFUND in categories
        assert EvidenceCategory.FEE in categories
        assert EvidenceCategory.ADJUSTMENT in categories
        assert EvidenceCategory.RECONCILIATION in categories
    finally:
        db.rollback()
        db.close()


def test_evidence_collector_missing_payment_exception():
    """Verify evidence correlation when internal payment record is absent (orphan settlement item)."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        assert merchant is not None

        run = ReconciliationRun(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            run_type="MANUAL_TRIGGER",
            status="COMPLETED",
            started_at=NOW,
            completed_at=NOW,
            total_records=1,
            matched_records=0,
            unmatched_records=1,
            exception_records=1,
        )
        db.add(run)
        db.flush()

        s = Settlement(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            external_id=f"setl_orphan_{uuid.uuid4().hex[:6]}",
            settlement_date=NOW.date(),
            amount=Decimal("1800.00"),
            currency="INR",
            status=SettlementStatus.SETTLED,
            source_created_at=NOW,
        )
        db.add(s)
        db.flush()

        si = SettlementItem(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            settlement_id=s.id,
            payment_id=None,
            external_payment_id=f"pay_unknown_{uuid.uuid4().hex[:6]}",
            gross_amount=Decimal("1800.00"),
            net_amount=Decimal("1764.00"),
            currency="INR",
            source_created_at=NOW,
        )
        db.add(si)
        db.flush()

        res = ReconciliationResult(
            id=uuid.uuid4(),
            run_id=run.id,
            merchant_id=merchant.id,
            payment_id=None,
            settlement_id=s.id,
            match_type=MatchType.UNMATCHED,
            match_status=MatchStatus.EXCEPTION,
            expected_amount=Decimal("0.00"),
            actual_amount=Decimal("1764.00"),
            difference=Decimal("-1764.00"),
            tolerance=Decimal("1.00"),
            confidence=Decimal("1.0000"),
            explanation="Unmatched settlement line item without internal payment",
            matching_fields={"settlement_item_id": str(si.id)},
        )
        db.add(res)
        db.flush()

        exc = ExceptionRecord(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            reconciliation_result_id=res.id,
            exception_type=ExceptionType.MISSING_PAYMENT,
            severity=ExceptionSeverity.MEDIUM,
            status=ExceptionStatus.OPEN,
            financial_impact=Decimal("1764.00"),
            currency="INR",
            description="Settlement item without matching payment in internal ledger",
        )
        db.add(exc)
        db.flush()

        collector = EvidenceCollector(db=db, merchant_id=merchant.id)
        raw = collector.collect(exception_id=exc.id)
        assert raw is not None
        assert raw.payment is None
        assert raw.settlement_item is not None

        evidence_resp = EvidenceCorrelator.correlate(raw)
        assert evidence_resp.summary.overall_strength == EvidenceStrength.INCOMPLETE
        assert any(
            "payment ledger record is missing" in m
            for m in evidence_resp.summary.missing_information
        )
        assert evidence_resp.summary.cause_established is True
    finally:
        db.rollback()
        db.close()


def test_evidence_collector_conflicting_duplicate_records():
    """Verify evidence handling when duplicate conflicting settlement items share external_payment_id."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        assert merchant is not None

        run = ReconciliationRun(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            run_type="MANUAL_TRIGGER",
            status="COMPLETED",
            started_at=NOW,
            completed_at=NOW,
            total_records=2,
            matched_records=0,
            unmatched_records=2,
            exception_records=2,
        )
        db.add(run)
        db.flush()

        s = Settlement(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            external_id=f"setl_dup_batch_{uuid.uuid4().hex[:6]}",
            settlement_date=NOW.date(),
            amount=Decimal("4000.00"),
            currency="INR",
            status=SettlementStatus.SETTLED,
            source_created_at=NOW,
        )
        db.add(s)
        db.flush()

        shared_ext_id = f"pay_collision_{uuid.uuid4().hex[:6]}"
        si1 = SettlementItem(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            settlement_id=s.id,
            external_payment_id=shared_ext_id,
            gross_amount=Decimal("2000.00"),
            net_amount=Decimal("1960.00"),
            currency="INR",
            source_created_at=NOW,
        )
        si2 = SettlementItem(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            settlement_id=s.id,
            external_payment_id=shared_ext_id,
            gross_amount=Decimal("2000.00"),
            net_amount=Decimal("1960.00"),
            currency="INR",
            source_created_at=NOW,
        )
        db.add_all([si1, si2])
        db.flush()

        res = ReconciliationResult(
            id=uuid.uuid4(),
            run_id=run.id,
            merchant_id=merchant.id,
            payment_id=None,
            settlement_id=s.id,
            match_type=MatchType.UNMATCHED,
            match_status=MatchStatus.EXCEPTION,
            expected_amount=Decimal("0.00"),
            actual_amount=Decimal("1960.00"),
            difference=Decimal("-1960.00"),
            tolerance=Decimal("1.00"),
            confidence=Decimal("1.0000"),
            explanation="Duplicate settlement line item detected",
            matching_fields={
                "reason": "duplicate_settlement",
                "settlement_item_id": str(si2.id),
            },
        )
        db.add(res)
        db.flush()

        exc = ExceptionRecord(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            reconciliation_result_id=res.id,
            exception_type=ExceptionType.DUPLICATE_SETTLEMENT,
            severity=ExceptionSeverity.HIGH,
            status=ExceptionStatus.OPEN,
            financial_impact=Decimal("1960.00"),
            currency="INR",
            description="Duplicate settlement line item detected in bank report",
        )
        db.add(exc)
        db.flush()

        collector = EvidenceCollector(db=db, merchant_id=merchant.id)
        raw = collector.collect(exception_id=exc.id)
        assert raw is not None
        assert len(raw.conflicting_items) == 1

        evidence_resp = EvidenceCorrelator.correlate(raw)
        assert evidence_resp.summary.overall_strength == EvidenceStrength.CONFLICTING
        assert len(evidence_resp.summary.conflicts) > 0
        assert any(
            item.strength == EvidenceStrength.CONFLICTING for item in evidence_resp.evidence_items
        )
    finally:
        db.rollback()
        db.close()


def test_evidence_api_endpoints_and_tenant_isolation():
    """Verify authenticated API endpoints, decimal serialization, and cross-tenant rejection."""
    db = SessionLocal()
    try:
        # Retrieve primary merchant and admin user
        merchant_a = db.query(Merchant).first()
        user_a = (
            db.query(User)
            .filter(User.merchant_id == merchant_a.id, User.role == UserRole.ADMIN)
            .first()
        )
        assert user_a is not None

        # Retrieve an existing exception for merchant_a
        exc_a = (
            db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant_a.id).first()
        )
        assert exc_a is not None

        # Create Merchant B and User B for tenant isolation test
        merchant_b = Merchant(
            id=uuid.uuid4(),
            name=f"Isolated Merchant {uuid.uuid4().hex[:6]}",
            email=f"merchant_b_{uuid.uuid4().hex[:6]}@example.com",
            currency="INR",
            timezone="Asia/Kolkata",
        )
        db.add(merchant_b)
        db.flush()

        user_b = User(
            id=uuid.uuid4(),
            merchant_id=merchant_b.id,
            email=f"operator_b_{uuid.uuid4().hex[:6]}@example.com",
            password_hash="argon2id_placeholder_hash",
            full_name="Tenant B Operator",
            role=UserRole.FINANCE_OPERATOR,
        )
        db.add(user_b)
        db.commit()

        token_a = create_access_token(
            data={
                "sub": str(user_a.id),
                "merchant_id": str(merchant_a.id),
                "role": user_a.role.value,
            },
            expires_delta=timedelta(minutes=30),
        )
        token_b = create_access_token(
            data={
                "sub": str(user_b.id),
                "merchant_id": str(merchant_b.id),
                "role": user_b.role.value,
            },
            expires_delta=timedelta(minutes=30),
        )

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 1. User A successfully accesses exception evidence
        resp_ev_a = client.get(f"/api/v1/exceptions/{exc_a.id}/evidence", headers=headers_a)
        assert resp_ev_a.status_code == 200
        data_ev = resp_ev_a.json()
        assert data_ev["success"] is True
        assert data_ev["data"]["exception_id"] == str(exc_a.id)
        assert "evidence_items" in data_ev["data"]
        assert "reconciliation" in data_ev["data"]
        assert "summary" in data_ev["data"]
        # Monetary decimal string check
        assert isinstance(data_ev["data"]["reconciliation"]["expected_amount"], str)
        assert isinstance(data_ev["data"]["reconciliation"]["actual_amount"], str)
        assert isinstance(data_ev["data"]["reconciliation"]["variance"], str)

        # 2. User A accesses evidence summary endpoint
        resp_sum_a = client.get(
            f"/api/v1/exceptions/{exc_a.id}/evidence/summary", headers=headers_a
        )
        assert resp_sum_a.status_code == 200
        data_sum = resp_sum_a.json()
        assert data_sum["success"] is True
        assert "observed_discrepancy" in data_sum["data"]
        assert "overall_strength" in data_sum["data"]

        # 3. User B (different tenant) attempts to access Merchant A's exception -> MUST 404
        resp_ev_b = client.get(f"/api/v1/exceptions/{exc_a.id}/evidence", headers=headers_b)
        assert resp_ev_b.status_code == 404

        resp_sum_b = client.get(
            f"/api/v1/exceptions/{exc_a.id}/evidence/summary", headers=headers_b
        )
        assert resp_sum_b.status_code == 404

        # 4. Nonexistent exception ID -> 404
        random_id = uuid.uuid4()
        resp_nonexistent = client.get(f"/api/v1/exceptions/{random_id}/evidence", headers=headers_a)
        assert resp_nonexistent.status_code == 404
    finally:
        db.rollback()
        db.close()
