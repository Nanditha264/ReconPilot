import uuid
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, NamedTuple

from app.models.enums import MatchStatus, MatchType
from app.modules.reconciliation.calculations import (
    calculate_expected_settlement_for_payment,
)
from app.modules.reconciliation.classification import (
    ClassificationResult,
    classify_matched_breakdown,
    classify_unmatched_payment,
    classify_unmatched_settlement_item,
)
from app.modules.reconciliation.constants import (
    DEFAULT_AMOUNT_TOLERANCE,
    DEFAULT_SETTLEMENT_DELAY_DAYS,
    MAX_CANDIDATE_DATE_WINDOW_DAYS,
    STAGE1_CONFIDENCE,
)
from app.modules.reconciliation.duplicate_detection import detect_duplicates
from app.modules.reconciliation.matching import run_deterministic_matching
from app.modules.reconciliation.normalization import (
    NormalizedAdjustment,
    NormalizedFee,
    NormalizedPayment,
    NormalizedRefund,
    NormalizedSettlementItem,
)


class EnginePlanResultItem(NamedTuple):
    payment_id: uuid.UUID | None
    settlement_id: uuid.UUID | None
    settlement_item_id: uuid.UUID | None
    match_type: MatchType
    match_status: MatchStatus
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    tolerance: Decimal
    confidence: Decimal
    explanation: str
    matching_fields: dict[str, Any]
    # Exception metadata if match_status == EXCEPTION
    classification: ClassificationResult | None


class EngineRunPlan(NamedTuple):
    results: list[EnginePlanResultItem]
    total_records: int
    matched_records: int
    unmatched_records: int
    exception_records: int
    auto_classified_records: int
    review_required_records: int
    duplicate_candidates: int
    ambiguous_candidates: int


def execute_reconciliation_plan(
    merchant_id: uuid.UUID,
    payments: list[NormalizedPayment],
    settlement_items: list[NormalizedSettlementItem],
    refunds: list[NormalizedRefund],
    fees: list[NormalizedFee],
    adjustments: list[NormalizedAdjustment],
    tolerance: Decimal = DEFAULT_AMOUNT_TOLERANCE,
    settlement_delay_days: int = DEFAULT_SETTLEMENT_DELAY_DAYS,
    date_window_days: int = MAX_CANDIDATE_DATE_WINDOW_DAYS,
    current_time: datetime | None = None,
) -> EngineRunPlan:
    """
    Pure deterministic reconciliation pipeline:
    1. Duplication detection
    2. Exact & strong relationship matching
    3. Monetary calculation with Decimal arithmetic
    4. Exception classification
    5. Aggregated plan counters
    """
    now = current_time or datetime.now(UTC)

    # 1. Duplicate detection
    dup_res = detect_duplicates(payments, settlement_items)

    # Group support records by payment_id
    refunds_by_payment: dict[uuid.UUID, list[NormalizedRefund]] = defaultdict(list)
    for r in refunds:
        refunds_by_payment[r.payment_id].append(r)

    fees_by_payment: dict[uuid.UUID, list[NormalizedFee]] = defaultdict(list)
    for f in fees:
        if f.payment_id:
            fees_by_payment[f.payment_id].append(f)

    adjustments_by_payment: dict[uuid.UUID, list[NormalizedAdjustment]] = defaultdict(list)
    for a in adjustments:
        if a.payment_id:
            adjustments_by_payment[a.payment_id].append(a)

    item_by_id = {item.id: item for item in settlement_items}
    payment_by_id = {p.id: p for p in payments}

    # 2. Matching
    matching = run_deterministic_matching(
        payments=payments,
        settlement_items=settlement_items,
        date_window_days=date_window_days,
    )

    plan_items: list[EnginePlanResultItem] = []
    matched_count = 0
    unmatched_count = 0
    exception_count = 0
    review_required_count = 0

    # 3. Process matched pairs
    for match in matching.matched_pairs:
        payment = payment_by_id[match.payment_id]
        item = item_by_id[match.settlement_item_id]

        p_refunds = refunds_by_payment.get(payment.id, [])
        p_fees = fees_by_payment.get(payment.id, [])
        p_adjs = adjustments_by_payment.get(payment.id, [])

        breakdown = calculate_expected_settlement_for_payment(
            payment=payment,
            refunds=p_refunds,
            fees=p_fees,
            adjustments=p_adjs,
            actual_item=item,
            tolerance=tolerance,
        )

        classification = classify_matched_breakdown(
            breakdown=breakdown,
            fees=p_fees,
            refunds=p_refunds,
            actual_item=item,
        )

        if classification.match_status in (MatchStatus.MATCHED, MatchStatus.MATCHED_WITH_VARIANCE):
            matched_count += 1
        else:
            exception_count += 1
            review_required_count += 1

        plan_items.append(
            EnginePlanResultItem(
                payment_id=payment.id,
                settlement_id=item.settlement_id,
                settlement_item_id=item.id,
                match_type=match.match_type,
                match_status=classification.match_status,
                expected_amount=breakdown.expected_settlement,
                actual_amount=breakdown.actual_settlement,
                difference=breakdown.difference,
                tolerance=tolerance,
                confidence=match.confidence,
                explanation=f"{match.explanation} {breakdown.explanation}",
                matching_fields={
                    **match.matching_fields,
                    "settlement_item_id": str(item.id),
                },
                classification=classification
                if classification.match_status == MatchStatus.EXCEPTION
                else None,
            )
        )

    # 4. Process unmatched payments (MISSING_SETTLEMENT / DELAYED_SETTLEMENT)
    for p_id in matching.unmatched_payment_ids:
        payment = payment_by_id[p_id]
        p_refunds = refunds_by_payment.get(payment.id, [])
        p_fees = fees_by_payment.get(payment.id, [])
        p_adjs = adjustments_by_payment.get(payment.id, [])

        breakdown = calculate_expected_settlement_for_payment(
            payment=payment,
            refunds=p_refunds,
            fees=p_fees,
            adjustments=p_adjs,
            actual_item=None,
            tolerance=tolerance,
        )

        is_dup_pay = p_id in dup_res.duplicate_payment_ids
        classification = classify_unmatched_payment(
            payment=payment,
            current_time=now,
            settlement_delay_days=settlement_delay_days,
            is_duplicate=is_dup_pay,
        )

        unmatched_count += 1
        exception_count += 1
        review_required_count += 1

        plan_items.append(
            EnginePlanResultItem(
                payment_id=payment.id,
                settlement_id=None,
                settlement_item_id=None,
                match_type=MatchType.UNMATCHED,
                match_status=MatchStatus.EXCEPTION,
                expected_amount=breakdown.expected_settlement,
                actual_amount=Decimal("0.00"),
                difference=breakdown.expected_settlement,
                tolerance=tolerance,
                confidence=STAGE1_CONFIDENCE,
                explanation=classification.description,
                matching_fields={
                    "reason": "duplicate_payment" if is_dup_pay else "unmatched_captured_payment"
                },
                classification=classification,
            )
        )

    # 5. Process unmatched settlement items (MISSING_PAYMENT / DUPLICATE_SETTLEMENT)
    for item_id in matching.unmatched_settlement_item_ids:
        item = item_by_id[item_id]
        is_dup_item = item_id in dup_res.duplicate_item_ids
        classification = classify_unmatched_settlement_item(
            item=item,
            is_duplicate=is_dup_item,
        )

        unmatched_count += 1
        exception_count += 1
        review_required_count += 1

        plan_items.append(
            EnginePlanResultItem(
                payment_id=None,
                settlement_id=item.settlement_id,
                settlement_item_id=item.id,
                match_type=MatchType.UNMATCHED,
                match_status=MatchStatus.EXCEPTION,
                expected_amount=Decimal("0.00"),
                actual_amount=item.net_amount,
                difference=-item.net_amount,
                tolerance=tolerance,
                confidence=STAGE1_CONFIDENCE,
                explanation=classification.description,
                matching_fields={
                    "reason": "unmatched_settlement_item",
                    "settlement_item_id": str(item.id),
                },
                classification=classification,
            )
        )

    total_records = len(payments) + len(settlement_items)

    return EngineRunPlan(
        results=plan_items,
        total_records=total_records,
        matched_records=matched_count,
        unmatched_records=unmatched_count,
        exception_records=exception_count,
        auto_classified_records=0,  # AI-assisted auto classification deferred to policy gate in Phase 05
        review_required_records=review_required_count,
        duplicate_candidates=len(dup_res.duplicate_payment_ids) + len(dup_res.duplicate_item_ids),
        ambiguous_candidates=len(matching.ambiguous_pairs),
    )
