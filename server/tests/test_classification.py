import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.enums import (
    ExceptionSeverity,
    ExceptionType,
    MatchStatus,
    PaymentStatus,
)
from app.modules.reconciliation.calculations import CalculationBreakdown
from app.modules.reconciliation.classification import (
    classify_matched_breakdown,
    classify_unmatched_payment,
    classify_unmatched_settlement_item,
)
from app.modules.reconciliation.normalization import (
    NormalizedPayment,
    NormalizedSettlementItem,
)

NOW = datetime.now(UTC)
MERCHANT_ID = uuid.uuid4()


def test_fee_mismatch_classification():
    item = NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        settlement_id=uuid.uuid4(),
        gross_amount=Decimal("1000.00"),
        fee_amount=Decimal("50.00"),  # Actual fee recorded
        net_amount=Decimal("950.00"),
        currency="INR",
        source_created_at=NOW,
    )
    # Expected fee is only 20.00 -> variance 30.00
    breakdown = CalculationBreakdown(
        original_payment_amount=Decimal("1000.00"),
        successful_refund_total=Decimal("0.00"),
        applicable_fee_total=Decimal("20.00"),
        applicable_adjustment_total=Decimal("0.00"),
        expected_settlement=Decimal("980.00"),
        actual_settlement=Decimal("950.00"),
        difference=Decimal("30.00"),
        currency="INR",
        applied_tolerance=Decimal("1.00"),
        is_within_tolerance=False,
        explanation="",
    )

    res = classify_matched_breakdown(breakdown, [], [], item)
    assert res.match_status == MatchStatus.EXCEPTION
    assert res.exception_type == ExceptionType.FEE_MISMATCH
    assert res.financial_impact == Decimal("30.00")


def test_refund_mismatch_classification():
    item = NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        settlement_id=uuid.uuid4(),
        gross_amount=Decimal("1000.00"),
        fee_amount=Decimal("20.00"),
        refund_amount=Decimal("200.00"),  # Actual refund in settlement
        net_amount=Decimal("780.00"),
        currency="INR",
        source_created_at=NOW,
    )
    # Expected refund is 0.00
    breakdown = CalculationBreakdown(
        original_payment_amount=Decimal("1000.00"),
        successful_refund_total=Decimal("0.00"),
        applicable_fee_total=Decimal("20.00"),
        applicable_adjustment_total=Decimal("0.00"),
        expected_settlement=Decimal("980.00"),
        actual_settlement=Decimal("780.00"),
        difference=Decimal("200.00"),
        currency="INR",
        applied_tolerance=Decimal("1.00"),
        is_within_tolerance=False,
        explanation="",
    )

    res = classify_matched_breakdown(breakdown, [], [], item)
    assert res.match_status == MatchStatus.EXCEPTION
    assert res.exception_type == ExceptionType.REFUND_MISMATCH
    assert res.financial_impact == Decimal("200.00")


def test_unmatched_payment_delayed_vs_missing():
    # 1. Payment created 5 days ago (delay threshold = 2 days) -> beyond SLA -> DELAYED_SETTLEMENT
    old_payment = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        external_id="pay_old",
        amount=Decimal("2500.00"),
        currency="INR",
        status=PaymentStatus.CAPTURED,
        payment_method="card",
        source_created_at=NOW - timedelta(days=5),
    )
    res_delayed = classify_unmatched_payment(old_payment, current_time=NOW, settlement_delay_days=2)
    assert res_delayed.exception_type == ExceptionType.DELAYED_SETTLEMENT
    assert res_delayed.financial_impact == Decimal("2500.00")

    # 2. Payment created 1 hour ago -> within 2-day SLA -> MISSING_SETTLEMENT
    recent_payment = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        external_id="pay_recent",
        amount=Decimal("2500.00"),
        currency="INR",
        status=PaymentStatus.CAPTURED,
        payment_method="card",
        source_created_at=NOW - timedelta(hours=1),
    )
    res_missing = classify_unmatched_payment(
        recent_payment, current_time=NOW, settlement_delay_days=2
    )
    assert res_missing.exception_type == ExceptionType.MISSING_SETTLEMENT
    assert res_missing.financial_impact == Decimal("2500.00")

    # 3. Exact SLA boundary (elapsed = exactly 2.0 days) -> within SLA boundary -> MISSING_SETTLEMENT
    boundary_payment = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        external_id="pay_boundary",
        amount=Decimal("3000.00"),
        currency="INR",
        status=PaymentStatus.CAPTURED,
        payment_method="card",
        source_created_at=NOW - timedelta(days=2),
    )
    res_boundary = classify_unmatched_payment(
        boundary_payment, current_time=NOW, settlement_delay_days=2
    )
    assert res_boundary.exception_type == ExceptionType.MISSING_SETTLEMENT

    # 4. Just beyond SLA boundary (elapsed = 2.01 days) -> beyond SLA -> DELAYED_SETTLEMENT
    just_overdue_payment = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        external_id="pay_just_overdue",
        amount=Decimal("3000.00"),
        currency="INR",
        status=PaymentStatus.CAPTURED,
        payment_method="card",
        source_created_at=NOW - timedelta(days=2, minutes=15),
    )
    res_just_overdue = classify_unmatched_payment(
        just_overdue_payment, current_time=NOW, settlement_delay_days=2
    )
    assert res_just_overdue.exception_type == ExceptionType.DELAYED_SETTLEMENT

    # 5. Non-captured payment (FAILED) -> expected settlement is 0.00, financial impact = 0.00
    failed_payment = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        external_id="pay_failed",
        amount=Decimal("1500.00"),
        currency="INR",
        status=PaymentStatus.FAILED,
        payment_method="upi",
        source_created_at=NOW - timedelta(days=4),
    )
    res_failed = classify_unmatched_payment(
        failed_payment, current_time=NOW, settlement_delay_days=2
    )
    assert res_failed.match_status == MatchStatus.EXCEPTION
    assert res_failed.exception_type == ExceptionType.UNKNOWN_EXCEPTION
    assert res_failed.financial_impact == Decimal("0.00")
    assert res_failed.severity == ExceptionSeverity.LOW

    # 6. Non-captured payment (AUTHORIZED) -> not captured, expected settlement 0.00, financial impact = 0.00
    authorized_payment = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        external_id="pay_authorized",
        amount=Decimal("2500.00"),
        currency="INR",
        status=PaymentStatus.AUTHORIZED,
        payment_method="card",
        source_created_at=NOW - timedelta(days=3),
    )
    res_auth = classify_unmatched_payment(
        authorized_payment, current_time=NOW, settlement_delay_days=2
    )
    assert res_auth.match_status == MatchStatus.EXCEPTION
    assert res_auth.exception_type == ExceptionType.UNKNOWN_EXCEPTION
    assert res_auth.financial_impact == Decimal("0.00")
    assert res_auth.severity == ExceptionSeverity.LOW


def test_unmatched_settlement_item_missing_payment():
    item = NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_ID,
        settlement_id=uuid.uuid4(),
        gross_amount=Decimal("1200.00"),
        net_amount=Decimal("1176.00"),
        currency="INR",
        source_created_at=NOW,
    )
    res = classify_unmatched_settlement_item(item)
    assert res.match_status == MatchStatus.EXCEPTION
    assert res.exception_type == ExceptionType.MISSING_PAYMENT
    assert res.financial_impact == Decimal("1176.00")
