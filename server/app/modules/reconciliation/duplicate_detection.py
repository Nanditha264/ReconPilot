import uuid
from collections import defaultdict
from typing import NamedTuple

from app.modules.reconciliation.normalization import (
    NormalizedPayment,
    NormalizedSettlementItem,
)


class DuplicateCheckResult(NamedTuple):
    duplicate_payment_ids: set[uuid.UUID]
    duplicate_item_ids: set[uuid.UUID]
    duplicate_external_ids: dict[str, list[uuid.UUID]]


def detect_duplicates(
    payments: list[NormalizedPayment],
    settlement_items: list[NormalizedSettlementItem],
) -> DuplicateCheckResult:
    """
    Identifies duplicate source records and external reference collisions.
    Does NOT mistake legitimate multiple payments of identical amounts as duplicates.
    Requires duplicate external_id or identical relationship keys to classify as true duplicates.
    """
    # 1. Check duplicate external_ids or duplicate external_order_ids across payments
    payments_by_ext_id: dict[str, list[uuid.UUID]] = defaultdict(list)
    payments_by_order_id: dict[str, list[uuid.UUID]] = defaultdict(list)
    duplicate_payment_ids: set[uuid.UUID] = set()

    for p in payments:
        if p.external_id:
            payments_by_ext_id[p.external_id].append(p.id)
        if p.external_order_id:
            payments_by_order_id[p.external_order_id].append(p.id)

    dup_ext_ids: dict[str, list[uuid.UUID]] = {}
    for ext_id, p_ids in payments_by_ext_id.items():
        if len(p_ids) > 1:
            dup_ext_ids[ext_id] = p_ids
            duplicate_payment_ids.update(p_ids[1:])

    for order_id, p_ids in payments_by_order_id.items():
        if len(p_ids) > 1:
            dup_ext_ids[f"order:{order_id}"] = p_ids
            duplicate_payment_ids.update(p_ids[1:])

    # 2. Check duplicate settlement line items referencing the same payment
    items_by_payment_id: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    items_by_ext_payment: dict[str, list[uuid.UUID]] = defaultdict(list)
    duplicate_item_ids: set[uuid.UUID] = set()

    for item in settlement_items:
        if item.payment_id:
            items_by_payment_id[item.payment_id].append(item.id)
        if item.external_payment_id:
            items_by_ext_payment[item.external_payment_id].append(item.id)

    for _p_id, item_ids in items_by_payment_id.items():
        if len(item_ids) > 1:
            duplicate_item_ids.update(item_ids[1:])

    for _ext_pay_id, item_ids in items_by_ext_payment.items():
        if len(item_ids) > 1:
            duplicate_item_ids.update(item_ids[1:])

    return DuplicateCheckResult(
        duplicate_payment_ids=duplicate_payment_ids,
        duplicate_item_ids=duplicate_item_ids,
        duplicate_external_ids=dup_ext_ids,
    )
