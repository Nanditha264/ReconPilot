import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AdjustmentStatus,
    AdjustmentType,
    FeeStatus,
    FeeType,
    PaymentStatus,
    RefundStatus,
    SettlementStatus,
)


class NormalizedPayment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    external_id: str
    external_order_id: str | None = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: str
    captured_at: datetime | None = None
    source_created_at: datetime
    payment_metadata: dict[str, Any] | None = Field(default=None, alias="payment_metadata")


class NormalizedRefund(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    payment_id: uuid.UUID
    external_id: str
    amount: Decimal
    currency: str
    status: RefundStatus
    processed_at: datetime
    refund_metadata: dict[str, Any] | None = Field(default=None, alias="refund_metadata")


class NormalizedFee(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    payment_id: uuid.UUID | None = None
    fee_type: FeeType
    amount: Decimal
    tax_amount: Decimal = Decimal("0.00")
    currency: str
    status: FeeStatus
    created_at: datetime


class NormalizedAdjustment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    payment_id: uuid.UUID | None = None
    settlement_id: uuid.UUID | None = None
    adjustment_type: AdjustmentType
    # Signed amount: positive increases expected settlement, negative decreases
    amount: Decimal
    currency: str
    status: AdjustmentStatus
    reason: str | None = None
    effective_at: datetime
    adjustment_metadata: dict[str, Any] | None = Field(default=None, alias="adjustment_metadata")


class NormalizedSettlementItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    settlement_id: uuid.UUID
    payment_id: uuid.UUID | None = None
    external_payment_id: str | None = None
    gross_amount: Decimal
    fee_amount: Decimal = Decimal("0.00")
    refund_amount: Decimal = Decimal("0.00")
    adjustment_amount: Decimal = Decimal("0.00")
    net_amount: Decimal
    currency: str
    source_created_at: datetime
    item_metadata: dict[str, Any] | None = Field(default=None, alias="item_metadata")


class NormalizedSettlement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    external_id: str
    amount: Decimal
    currency: str
    status: SettlementStatus
    settled_at: datetime | None = None
    source_created_at: datetime
    items: list[NormalizedSettlementItem] = Field(default_factory=list)
