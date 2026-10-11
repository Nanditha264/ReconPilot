import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.models.enums import MatchType
from app.modules.reconciliation.constants import (
    STAGE1_CONFIDENCE,
    STAGE2_CONFIDENCE,
)
from app.modules.reconciliation.matching import run_deterministic_matching
from app.modules.reconciliation.normalization import (
    NormalizedPayment,
    NormalizedSettlementItem,
)

NOW = datetime.now(UTC)
MERCHANT_A = uuid.uuid4()
MERCHANT_B = uuid.uuid4()


def test_stage1_exact_payment_id_match():
    payment_id = uuid.uuid4()
    p = NormalizedPayment(
        id=payment_id,
        merchant_id=MERCHANT_A,
        external_id="pay_101",
        amount=Decimal("1500.00"),
        currency="INR",
        status="CAPTURED",  # type: ignore[arg-type]
        payment_method="card",
        source_created_at=NOW,
    )
    item = NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_A,
        settlement_id=uuid.uuid4(),
        payment_id=payment_id,
        gross_amount=Decimal("1500.00"),
        net_amount=Decimal("1470.00"),
        currency="INR",
        source_created_at=NOW,
    )

    result = run_deterministic_matching([p], [item])
    assert len(result.matched_pairs) == 1
    assert result.matched_pairs[0].match_type == MatchType.EXACT_2_WAY
    assert result.matched_pairs[0].confidence == STAGE1_CONFIDENCE
    assert result.matched_pairs[0].matching_fields["rule"] == "internal_payment_id"


def test_stage1_exact_external_payment_id_match():
    p = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_A,
        external_id="pay_ext_999",
        amount=Decimal("2000.00"),
        currency="INR",
        status="CAPTURED",  # type: ignore[arg-type]
        payment_method="upi",
        source_created_at=NOW,
    )
    # Settlement item has no internal payment_id, but has external_payment_id matching
    item = NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_A,
        settlement_id=uuid.uuid4(),
        payment_id=None,
        external_payment_id="pay_ext_999",
        gross_amount=Decimal("2000.00"),
        net_amount=Decimal("1960.00"),
        currency="INR",
        source_created_at=NOW,
    )

    result = run_deterministic_matching([p], [item])
    assert len(result.matched_pairs) == 1
    assert result.matched_pairs[0].confidence == STAGE1_CONFIDENCE
    assert result.matched_pairs[0].matching_fields["rule"] == "external_payment_id"


def test_stage2_strong_match_by_amount_and_timestamp():
    p = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_A,
        external_id="pay_diff_ref",
        amount=Decimal("3500.00"),
        currency="INR",
        status="CAPTURED",  # type: ignore[arg-type]
        payment_method="card",
        source_created_at=NOW,
    )
    item = NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_A,
        settlement_id=uuid.uuid4(),
        payment_id=None,
        external_payment_id="unrelated_ref",
        gross_amount=Decimal("3500.00"),
        net_amount=Decimal("3430.00"),
        currency="INR",
        source_created_at=NOW,
    )

    result = run_deterministic_matching([p], [item])
    assert len(result.matched_pairs) == 1
    assert result.matched_pairs[0].match_type == MatchType.TOLERANCE_2_WAY
    assert result.matched_pairs[0].confidence == STAGE2_CONFIDENCE


def test_cross_merchant_isolation_blocks_matching():
    # Payment belongs to MERCHANT_A, settlement item belongs to MERCHANT_B
    payment_id = uuid.uuid4()
    p = NormalizedPayment(
        id=payment_id,
        merchant_id=MERCHANT_A,
        external_id="pay_isolated",
        amount=Decimal("1000.00"),
        currency="INR",
        status="CAPTURED",  # type: ignore[arg-type]
        payment_method="card",
        source_created_at=NOW,
    )
    item = NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_B,
        settlement_id=uuid.uuid4(),
        payment_id=payment_id,
        gross_amount=Decimal("1000.00"),
        net_amount=Decimal("980.00"),
        currency="INR",
        source_created_at=NOW,
    )

    result = run_deterministic_matching([p], [item])
    # Must NOT match cross-merchant!
    assert len(result.matched_pairs) == 0
    assert payment_id in result.unmatched_payment_ids
    assert item.id in result.unmatched_settlement_item_ids


def test_ambiguous_candidate_detection():
    # Multiple payments with exact same amount in same merchant
    p1 = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_A,
        external_id="pay_amb_1",
        amount=Decimal("500.00"),
        currency="INR",
        status="CAPTURED",  # type: ignore[arg-type]
        payment_method="card",
        source_created_at=NOW,
    )
    p2 = NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_A,
        external_id="pay_amb_2",
        amount=Decimal("500.00"),
        currency="INR",
        status="CAPTURED",  # type: ignore[arg-type]
        payment_method="card",
        source_created_at=NOW,
    )
    item = NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=MERCHANT_A,
        settlement_id=uuid.uuid4(),
        payment_id=None,
        external_payment_id=None,
        gross_amount=Decimal("500.00"),
        net_amount=Decimal("490.00"),
        currency="INR",
        source_created_at=NOW,
    )

    result = run_deterministic_matching([p1, p2], [item])
    # Refuses to force a match; flags ambiguity
    assert len(result.matched_pairs) == 0
    assert len(result.ambiguous_pairs) == 1
