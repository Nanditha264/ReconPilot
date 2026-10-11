import uuid
from decimal import Decimal
from typing import NamedTuple

from app.models.enums import MatchType
from app.modules.reconciliation.constants import (
    STAGE1_CONFIDENCE,
    STAGE2_CONFIDENCE,
)
from app.modules.reconciliation.normalization import (
    NormalizedPayment,
    NormalizedSettlementItem,
)


class MatchCandidate(NamedTuple):
    payment_id: uuid.UUID
    settlement_item_id: uuid.UUID
    match_type: MatchType
    confidence: Decimal
    matching_fields: dict[str, str]
    explanation: str


class MatchingResult(NamedTuple):
    # Matched pairs: list of MatchCandidate
    matched_pairs: list[MatchCandidate]
    # Unmatched payment IDs
    unmatched_payment_ids: set[uuid.UUID]
    # Unmatched settlement item IDs
    unmatched_settlement_item_ids: set[uuid.UUID]
    # Ambiguous candidate pairs detected (flagged for review, not forced)
    ambiguous_pairs: list[dict[str, str]]


def run_deterministic_matching(
    payments: list[NormalizedPayment],
    settlement_items: list[NormalizedSettlementItem],
    date_window_days: int = 7,
) -> MatchingResult:
    """
    Executes 3-stage deterministic reconciliation matching:
    Stage 1: Exact relationship matching (payment.id == item.payment_id OR payment.external_id == item.external_payment_id)
    Stage 2: Strong reference matching (merchant + currency + exact gross amount within date window)
    Stage 3: Controlled candidate matching with ambiguity detection (refuses to force ambiguous candidates)
    """
    matched_pairs: list[MatchCandidate] = []
    matched_payment_ids: set[uuid.UUID] = set()
    matched_item_ids: set[uuid.UUID] = set()
    ambiguous_pairs: list[dict[str, str]] = []

    # Fast lookup indexes for payments
    payment_by_id = {p.id: p for p in payments}
    payment_by_ext_id = {p.external_id: p for p in payments if p.external_id}

    # =========================================================================
    # STAGE 1: Exact relationship matching
    # =========================================================================
    for item in settlement_items:
        # Check merchant & currency isolation
        if item.id in matched_item_ids:
            continue

        target_payment: NormalizedPayment | None = None
        matched_rule = ""

        # 1.a Direct internal payment ID link
        if item.payment_id and item.payment_id in payment_by_id:
            candidate = payment_by_id[item.payment_id]
            if candidate.merchant_id == item.merchant_id and candidate.currency == item.currency:
                target_payment = candidate
                matched_rule = "internal_payment_id"

        # 1.b External payment ID link
        elif item.external_payment_id and item.external_payment_id in payment_by_ext_id:
            candidate = payment_by_ext_id[item.external_payment_id]
            if candidate.merchant_id == item.merchant_id and candidate.currency == item.currency:
                target_payment = candidate
                matched_rule = "external_payment_id"

        if target_payment and target_payment.id not in matched_payment_ids:
            matched_payment_ids.add(target_payment.id)
            matched_item_ids.add(item.id)
            matched_pairs.append(
                MatchCandidate(
                    payment_id=target_payment.id,
                    settlement_item_id=item.id,
                    match_type=MatchType.EXACT_2_WAY,
                    confidence=STAGE1_CONFIDENCE,
                    matching_fields={
                        "rule": matched_rule,
                        "merchant_id": str(item.merchant_id),
                        "currency": item.currency,
                        "external_payment_id": item.external_payment_id or "",
                    },
                    explanation=f"Exact match via {matched_rule}.",
                )
            )

    # Remaining unmatched pools
    remaining_payments = [p for p in payments if p.id not in matched_payment_ids]
    remaining_items = [item for item in settlement_items if item.id not in matched_item_ids]

    # =========================================================================
    # STAGE 2: Strong reference matching (order reference / exact amount + date)
    # =========================================================================
    # Group remaining payments by (merchant_id, currency, gross_amount)
    for item in list(remaining_items):
        if item.id in matched_item_ids:
            continue

        # Look for candidates with same merchant, currency, and gross amount
        candidates = [
            p
            for p in remaining_payments
            if p.id not in matched_payment_ids
            and p.merchant_id == item.merchant_id
            and p.currency == item.currency
            and p.amount == item.gross_amount
            and abs((p.source_created_at - item.source_created_at).total_seconds())
            <= date_window_days * 86400
        ]

        if len(candidates) == 1:
            p = candidates[0]
            matched_payment_ids.add(p.id)
            matched_item_ids.add(item.id)
            matched_pairs.append(
                MatchCandidate(
                    payment_id=p.id,
                    settlement_item_id=item.id,
                    match_type=MatchType.TOLERANCE_2_WAY,
                    confidence=STAGE2_CONFIDENCE,
                    matching_fields={
                        "rule": "exact_amount_and_timestamp_window",
                        "merchant_id": str(item.merchant_id),
                        "currency": item.currency,
                        "amount": str(item.gross_amount),
                    },
                    explanation="Strong match on merchant, currency, amount, and close creation timestamps.",
                )
            )
        elif len(candidates) > 1:
            # Ambiguous: multiple payments match the same amount in the same timeframe
            ambiguous_pairs.append(
                {
                    "settlement_item_id": str(item.id),
                    "candidate_payment_ids": [str(c.id) for c in candidates],
                    "reason": f"Multiple ({len(candidates)}) payments have exact same amount {item.gross_amount} {item.currency}",
                }
            )

    # =========================================================================
    # STAGE 3: Final candidate set calculation
    # =========================================================================
    unmatched_payment_ids = {p.id for p in payments if p.id not in matched_payment_ids}
    unmatched_settlement_item_ids = {
        item.id for item in settlement_items if item.id not in matched_item_ids
    }

    return MatchingResult(
        matched_pairs=matched_pairs,
        unmatched_payment_ids=unmatched_payment_ids,
        unmatched_settlement_item_ids=unmatched_settlement_item_ids,
        ambiguous_pairs=ambiguous_pairs,
    )
