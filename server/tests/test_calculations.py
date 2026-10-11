import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.models.enums import (
    AdjustmentStatus,
    AdjustmentType,
    FeeStatus,
    FeeType,
    PaymentStatus,
    RefundStatus,
)
from app.modules.reconciliation.calculations import (
    calculate_expected_settlement_for_payment,
)
from app.modules.reconciliation.normalization import (
    NormalizedAdjustment,
    NormalizedFee,
    NormalizedPayment,
    NormalizedRefund,
    NormalizedSettlementItem,
)

NOW = datetime.now(UTC)
DUMMY_MERCHANT_ID = uuid.uuid4()


def make_payment(
    amount: str, status: PaymentStatus = PaymentStatus.CAPTURED, currency: str = "INR"
):
    return NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        external_id=f"pay_{uuid.uuid4().hex[:8]}",
        amount=Decimal(amount),
        currency=currency,
        status=status,
        payment_method="card",
        captured_at=NOW,
        source_created_at=NOW,
    )


def make_item(net_amount: str, currency: str = "INR", gross_amount: str = "0.00"):
    return NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        settlement_id=uuid.uuid4(),
        gross_amount=Decimal(gross_amount),
        net_amount=Decimal(net_amount),
        currency=currency,
        source_created_at=NOW,
    )


def test_standard_matched_calculation():
    # ₹5,000 payment, ₹500 refund, ₹100 fee, ₹0 adj -> expected ₹4,400. Actual ₹4,400 -> diff 0.
    p = make_payment("5000.00")
    r = NormalizedRefund(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        external_id="rfnd_1",
        amount=Decimal("500.00"),
        currency="INR",
        status=RefundStatus.PROCESSED,
        processed_at=NOW,
    )
    f = NormalizedFee(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        fee_type=FeeType.MDR,
        amount=Decimal("100.00"),
        tax_amount=Decimal("18.00"),
        currency="INR",
        status=FeeStatus.ASSESSED,
        created_at=NOW,
    )
    item = make_item(net_amount="4400.00")

    res = calculate_expected_settlement_for_payment(p, [r], [f], [], item)
    assert res.expected_settlement == Decimal("4400.00")
    assert res.difference == Decimal("0.00")
    assert res.is_within_tolerance is True


def test_under_settlement_positive_difference():
    # Expected ₹4,400, actual ₹4,300 -> diff = ₹100.00 (under-settled)
    p = make_payment("5000.00")
    r = NormalizedRefund(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        external_id="rfnd_1",
        amount=Decimal("500.00"),
        currency="INR",
        status=RefundStatus.PROCESSED,
        processed_at=NOW,
    )
    f = NormalizedFee(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        fee_type=FeeType.MDR,
        amount=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        currency="INR",
        status=FeeStatus.ASSESSED,
        created_at=NOW,
    )
    item = make_item(net_amount="4300.00")

    res = calculate_expected_settlement_for_payment(p, [r], [f], [], item)
    assert res.expected_settlement == Decimal("4400.00")
    assert res.actual_settlement == Decimal("4300.00")
    assert res.difference == Decimal("100.00")
    assert res.is_within_tolerance is False


def test_multiple_partial_refunds():
    p = make_payment("1000.00")
    r1 = NormalizedRefund(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        external_id="rfnd_1",
        amount=Decimal("150.00"),
        currency="INR",
        status=RefundStatus.PROCESSED,
        processed_at=NOW,
    )
    r2 = NormalizedRefund(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        external_id="rfnd_2",
        amount=Decimal("200.00"),
        currency="INR",
        status=RefundStatus.PROCESSED,
        processed_at=NOW,
    )
    res = calculate_expected_settlement_for_payment(p, [r1, r2], [], [])
    assert res.successful_refund_total == Decimal("350.00")
    assert res.expected_settlement == Decimal("650.00")


def test_failed_refund_excluded():
    p = make_payment("1000.00")
    r_failed = NormalizedRefund(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        external_id="rfnd_fail",
        amount=Decimal("300.00"),
        currency="INR",
        status=RefundStatus.FAILED,
        processed_at=NOW,
    )
    res = calculate_expected_settlement_for_payment(p, [r_failed], [], [])
    assert res.successful_refund_total == Decimal("0.00")
    assert res.expected_settlement == Decimal("1000.00")


def test_failed_payment_produces_zero_captured_revenue():
    p = make_payment("2000.00", status=PaymentStatus.FAILED)
    res = calculate_expected_settlement_for_payment(p, [], [], [])
    assert res.original_payment_amount == Decimal("0.00")
    assert res.expected_settlement == Decimal("0.00")


def test_positive_and_negative_adjustments():
    p = make_payment("1000.00")
    adj_pos = NormalizedAdjustment(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        adjustment_type=AdjustmentType.GOODWILL_CREDIT,
        amount=Decimal("50.00"),
        currency="INR",
        status=AdjustmentStatus.APPLIED,
        effective_at=NOW,
    )
    res_pos = calculate_expected_settlement_for_payment(p, [], [], [adj_pos])
    assert res_pos.expected_settlement == Decimal("1050.00")

    adj_neg = NormalizedAdjustment(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        adjustment_type=AdjustmentType.PENALTY,
        amount=Decimal("-30.00"),
        currency="INR",
        status=AdjustmentStatus.APPLIED,
        effective_at=NOW,
    )
    res_neg = calculate_expected_settlement_for_payment(p, [], [], [adj_neg])
    assert res_neg.expected_settlement == Decimal("970.00")


def test_currency_mismatch_raises_error():
    p = make_payment("1000.00", currency="INR")
    r_usd = NormalizedRefund(
        id=uuid.uuid4(),
        merchant_id=DUMMY_MERCHANT_ID,
        payment_id=p.id,
        external_id="rfnd_usd",
        amount=Decimal("10.00"),
        currency="USD",
        status=RefundStatus.PROCESSED,
        processed_at=NOW,
    )
    with pytest.raises(ValueError, match="Refund currency USD does not match"):
        calculate_expected_settlement_for_payment(p, [r_usd], [], [])


def test_exact_tolerance_boundaries():
    p = make_payment("1000.00")
    # Diff of exactly 1.00 is within 1.00 tolerance
    item_edge = make_item(net_amount="999.00")
    res_edge = calculate_expected_settlement_for_payment(
        p, [], [], [], item_edge, tolerance=Decimal("1.00")
    )
    assert res_edge.is_within_tolerance is True

    # Diff of 1.01 is outside 1.00 tolerance
    item_out = make_item(net_amount="998.99")
    res_out = calculate_expected_settlement_for_payment(
        p, [], [], [], item_out, tolerance=Decimal("1.00")
    )
    assert res_out.is_within_tolerance is False
