from datetime import UTC, datetime
from decimal import Decimal
from typing import NamedTuple

from app.models.enums import (
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    MatchStatus,
    PaymentStatus,
)
from app.modules.reconciliation.calculations import CalculationBreakdown
from app.modules.reconciliation.normalization import (
    NormalizedFee,
    NormalizedPayment,
    NormalizedRefund,
    NormalizedSettlementItem,
)


class ClassificationResult(NamedTuple):
    match_status: MatchStatus
    exception_type: ExceptionType | None
    severity: ExceptionSeverity | None
    exception_status: ExceptionStatus | None
    financial_impact: Decimal
    description: str


def classify_matched_breakdown(
    breakdown: CalculationBreakdown,
    fees: list[NormalizedFee],
    refunds: list[NormalizedRefund],
    actual_item: NormalizedSettlementItem,
) -> ClassificationResult:
    """
    Classifies a matched payment-settlement pair into MATCHED, MATCHED_WITH_VARIANCE,
    or specific ExceptionType (FEE_MISMATCH, REFUND_MISMATCH, AMOUNT_MISMATCH, etc.).
    """
    diff = breakdown.difference

    # 1. Perfectly within tolerance
    if breakdown.is_within_tolerance:
        if abs(diff) > Decimal("0.00"):
            return ClassificationResult(
                match_status=MatchStatus.MATCHED_WITH_VARIANCE,
                exception_type=None,
                severity=None,
                exception_status=None,
                financial_impact=abs(diff),
                description=f"Matched with minor variance {diff} within tolerance {breakdown.applied_tolerance}.",
            )
        return ClassificationResult(
            match_status=MatchStatus.MATCHED,
            exception_type=None,
            severity=None,
            exception_status=None,
            financial_impact=Decimal("0.00"),
            description="Perfect deterministic match.",
        )

    # 2. Beyond tolerance: determine specific root cause
    financial_impact = abs(diff)

    # Check fee mismatch: settlement item fee != sum of assessed fee records
    expected_fee_total = breakdown.applicable_fee_total
    actual_fee = actual_item.fee_amount
    if abs(expected_fee_total - actual_fee) > breakdown.applied_tolerance:
        severity = (
            ExceptionSeverity.MEDIUM
            if financial_impact < Decimal("500.00")
            else ExceptionSeverity.HIGH
        )
        return ClassificationResult(
            match_status=MatchStatus.EXCEPTION,
            exception_type=ExceptionType.FEE_MISMATCH,
            severity=severity,
            exception_status=ExceptionStatus.OPEN,
            financial_impact=financial_impact,
            description=(
                f"Fee mismatch: recorded fee in settlement is {actual_fee} {breakdown.currency}, "
                f"but applicable assessed fees sum to {expected_fee_total} {breakdown.currency}. "
                f"Variance: {diff}."
            ),
        )

    # Check refund mismatch: settlement item refund != sum of processed refund records
    expected_refund_total = breakdown.successful_refund_total
    actual_refund = actual_item.refund_amount
    if abs(expected_refund_total - actual_refund) > breakdown.applied_tolerance:
        severity = (
            ExceptionSeverity.HIGH
            if financial_impact >= Decimal("500.00")
            else ExceptionSeverity.MEDIUM
        )
        return ClassificationResult(
            match_status=MatchStatus.EXCEPTION,
            exception_type=ExceptionType.REFUND_MISMATCH,
            severity=severity,
            exception_status=ExceptionStatus.OPEN,
            financial_impact=financial_impact,
            description=(
                f"Refund mismatch: recorded refund in settlement is {actual_refund} {breakdown.currency}, "
                f"but processed refunds sum to {expected_refund_total} {breakdown.currency}. "
                f"Variance: {diff}."
            ),
        )

    # Check adjustment mismatch
    expected_adj_total = breakdown.applicable_adjustment_total
    actual_adj = actual_item.adjustment_amount
    if abs(expected_adj_total - actual_adj) > breakdown.applied_tolerance:
        return ClassificationResult(
            match_status=MatchStatus.EXCEPTION,
            exception_type=ExceptionType.ADJUSTMENT_MISMATCH,
            severity=ExceptionSeverity.MEDIUM,
            exception_status=ExceptionStatus.OPEN,
            financial_impact=financial_impact,
            description=(
                f"Adjustment mismatch: recorded adjustment in settlement is {actual_adj} {breakdown.currency}, "
                f"while applicable adjustments sum to {expected_adj_total} {breakdown.currency}."
            ),
        )

    # Default to general amount mismatch
    severity = (
        ExceptionSeverity.CRITICAL
        if financial_impact >= Decimal("5000.00")
        else (
            ExceptionSeverity.HIGH
            if financial_impact >= Decimal("500.00")
            else ExceptionSeverity.MEDIUM
        )
    )
    return ClassificationResult(
        match_status=MatchStatus.EXCEPTION,
        exception_type=ExceptionType.AMOUNT_MISMATCH,
        severity=severity,
        exception_status=ExceptionStatus.OPEN,
        financial_impact=financial_impact,
        description=(
            f"Gross amount mismatch: expected settlement is {breakdown.expected_settlement} {breakdown.currency}, "
            f"but actual settlement is {breakdown.actual_settlement} {breakdown.currency}. Difference: {diff}."
        ),
    )


def classify_unmatched_payment(
    payment: NormalizedPayment,
    current_time: datetime | None = None,
    settlement_delay_days: int = 2,
    is_duplicate: bool = False,
) -> ClassificationResult:
    """
    Classifies a payment that lacks any corresponding settlement item.
    - If payment is a duplicate payment submission / collision: DUPLICATE_PAYMENT.
    - If payment was NOT captured (e.g. FAILED, AUTHORIZED), expected settlement is 0.00,
      so financial impact is 0.00 and severity is LOW.
    - If payment was CAPTURED:
      - Within SLA window (elapsed_days <= settlement_delay_days): MISSING_SETTLEMENT (pending/open within SLA window).
      - Beyond SLA window (elapsed_days > settlement_delay_days): DELAYED_SETTLEMENT (overdue settlement past SLA).
    """
    if is_duplicate:
        return ClassificationResult(
            match_status=MatchStatus.EXCEPTION,
            exception_type=ExceptionType.DUPLICATE_PAYMENT,
            severity=ExceptionSeverity.HIGH,
            exception_status=ExceptionStatus.OPEN,
            financial_impact=payment.amount,
            description=f"Duplicate payment transaction detected for external ID {payment.external_id}.",
        )

    now = current_time or datetime.now(UTC)
    elapsed_seconds = (now - payment.source_created_at).total_seconds()
    elapsed_days = elapsed_seconds / 86400.0

    is_captured = payment.status == PaymentStatus.CAPTURED
    financial_impact = payment.amount if is_captured else Decimal("0.00")

    if not is_captured:
        return ClassificationResult(
            match_status=MatchStatus.EXCEPTION,
            exception_type=ExceptionType.UNKNOWN_EXCEPTION,
            severity=ExceptionSeverity.LOW,
            exception_status=ExceptionStatus.OPEN,
            financial_impact=Decimal("0.00"),
            description=f"Non-captured payment {payment.external_id} with status {payment.status.value} has no settlement credit expected.",
        )

    if financial_impact >= Decimal("5000.00"):
        severity = ExceptionSeverity.CRITICAL
    elif financial_impact >= Decimal("1000.00"):
        severity = ExceptionSeverity.HIGH
    else:
        severity = ExceptionSeverity.MEDIUM

    if elapsed_days > settlement_delay_days:
        return ClassificationResult(
            match_status=MatchStatus.EXCEPTION,
            exception_type=ExceptionType.DELAYED_SETTLEMENT,
            severity=severity,
            exception_status=ExceptionStatus.OPEN,
            financial_impact=financial_impact,
            description=(
                f"Delayed settlement: payment {payment.external_id} was captured {elapsed_days:.1f} days ago "
                f"(exceeding {settlement_delay_days}-day settlement SLA) without settlement credit."
            ),
        )

    return ClassificationResult(
        match_status=MatchStatus.EXCEPTION,
        exception_type=ExceptionType.MISSING_SETTLEMENT,
        severity=severity,
        exception_status=ExceptionStatus.OPEN,
        financial_impact=financial_impact,
        description=(
            f"Missing settlement: captured payment {payment.external_id} of {payment.amount} {payment.currency} "
            f"has no settlement batch record (within {settlement_delay_days}-day SLA window)."
        ),
    )


def classify_unmatched_settlement_item(
    item: NormalizedSettlementItem,
    is_duplicate: bool = False,
) -> ClassificationResult:
    """
    Classifies a settlement line item that cannot be tied to any internal payment record.
    """
    if is_duplicate:
        return ClassificationResult(
            match_status=MatchStatus.EXCEPTION,
            exception_type=ExceptionType.DUPLICATE_SETTLEMENT,
            severity=ExceptionSeverity.HIGH,
            exception_status=ExceptionStatus.OPEN,
            financial_impact=item.net_amount,
            description=f"Duplicate settlement entry detected for item {item.id} referencing payment {item.external_payment_id}.",
        )

    financial_impact = item.net_amount
    severity = (
        ExceptionSeverity.CRITICAL
        if financial_impact >= Decimal("5000.00")
        else (
            ExceptionSeverity.HIGH
            if financial_impact >= Decimal("1000.00")
            else ExceptionSeverity.MEDIUM
        )
    )

    return ClassificationResult(
        match_status=MatchStatus.EXCEPTION,
        exception_type=ExceptionType.MISSING_PAYMENT,
        severity=severity,
        exception_status=ExceptionStatus.OPEN,
        financial_impact=financial_impact,
        description=(
            f"Missing payment: settlement line item of {item.net_amount} {item.currency} "
            f"(external reference: {item.external_payment_id or 'NONE'}) has no corresponding internal payment."
        ),
    )
