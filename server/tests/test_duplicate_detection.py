import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.models.enums import PaymentStatus
from app.modules.reconciliation.duplicate_detection import detect_duplicates
from app.modules.reconciliation.normalization import (
    NormalizedPayment,
    NormalizedSettlementItem,
)

NOW = datetime.now(UTC)
MERCHANT_A = uuid.uuid4()
MERCHANT_B = uuid.uuid4()


def make_payment(
    external_id: str | None = None,
    external_order_id: str | None = None,
    amount: str = "1000.00",
    merchant_id: uuid.UUID = MERCHANT_A,
) -> NormalizedPayment:
    return NormalizedPayment(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        external_id=external_id,
        external_order_id=external_order_id,
        amount=Decimal(amount),
        currency="INR",
        status=PaymentStatus.CAPTURED,
        payment_method="card",
        captured_at=NOW,
        source_created_at=NOW,
    )


def make_item(
    payment_id: uuid.UUID | None = None,
    external_payment_id: str | None = None,
    net_amount: str = "980.00",
    settlement_id: uuid.UUID | None = None,
    merchant_id: uuid.UUID = MERCHANT_A,
) -> NormalizedSettlementItem:
    return NormalizedSettlementItem(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        settlement_id=settlement_id or uuid.uuid4(),
        payment_id=payment_id,
        external_payment_id=external_payment_id,
        gross_amount=Decimal("1000.00"),
        net_amount=Decimal(net_amount),
        currency="INR",
        source_created_at=NOW,
    )


def test_duplicate_payment_by_external_payment_id():
    """Duplicate external_id across two payments flags the second as duplicate."""
    p1 = make_payment(external_id="pay_dup_001")
    p2 = make_payment(external_id="pay_dup_001")

    res = detect_duplicates(payments=[p1, p2], settlement_items=[])
    assert p2.id in res.duplicate_payment_ids
    assert p1.id not in res.duplicate_payment_ids
    assert "pay_dup_001" in res.duplicate_external_ids


def test_duplicate_payment_by_external_order_id():
    """Duplicate external_order_id flags duplicate payment."""
    p1 = make_payment(external_id="pay_001", external_order_id="ord_dup_999")
    p2 = make_payment(external_id="pay_002", external_order_id="ord_dup_999")

    res = detect_duplicates(payments=[p1, p2], settlement_items=[])
    assert p2.id in res.duplicate_payment_ids
    assert "order:ord_dup_999" in res.duplicate_external_ids


def test_multiple_legitimate_payments_same_amount_different_orders():
    """Payments with identical amounts but distinct order and payment IDs are NOT duplicates."""
    p1 = make_payment(external_id="pay_101", external_order_id="ord_101", amount="500.00")
    p2 = make_payment(external_id="pay_102", external_order_id="ord_102", amount="500.00")

    res = detect_duplicates(payments=[p1, p2], settlement_items=[])
    assert len(res.duplicate_payment_ids) == 0
    assert len(res.duplicate_external_ids) == 0


def test_duplicate_settlement_items_linked_to_same_payment():
    """Multiple settlement items referencing the same payment ID or external payment ID."""
    p = make_payment(external_id="pay_201")
    i1 = make_item(payment_id=p.id, external_payment_id="pay_201")
    i2 = make_item(payment_id=p.id, external_payment_id="pay_201")

    res = detect_duplicates(payments=[p], settlement_items=[i1, i2])
    assert i2.id in res.duplicate_item_ids
    assert i1.id not in res.duplicate_item_ids


def test_multiple_legitimate_items_within_one_settlement_batch():
    """Multiple settlement items within the same settlement referencing distinct payments are valid."""
    batch_settlement_id = uuid.uuid4()
    p1 = make_payment(external_id="pay_301")
    p2 = make_payment(external_id="pay_302")

    i1 = make_item(
        payment_id=p1.id, external_payment_id="pay_301", settlement_id=batch_settlement_id
    )
    i2 = make_item(
        payment_id=p2.id, external_payment_id="pay_302", settlement_id=batch_settlement_id
    )

    res = detect_duplicates(payments=[p1, p2], settlement_items=[i1, i2])
    assert len(res.duplicate_item_ids) == 0
    assert len(res.duplicate_payment_ids) == 0


def test_merchant_isolation_for_external_identifiers():
    """Same external_id across different merchants does not cross-pollute when processed per merchant."""
    p_merchant_a = make_payment(external_id="pay_shared_ext", merchant_id=MERCHANT_A)
    p_merchant_b = make_payment(external_id="pay_shared_ext", merchant_id=MERCHANT_B)

    # Reconciliation runs are scoped per merchant
    res_a = detect_duplicates(payments=[p_merchant_a], settlement_items=[])
    res_b = detect_duplicates(payments=[p_merchant_b], settlement_items=[])

    assert len(res_a.duplicate_payment_ids) == 0
    assert len(res_b.duplicate_payment_ids) == 0
