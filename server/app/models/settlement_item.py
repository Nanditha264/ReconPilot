import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.settlement import Settlement


class SettlementItem(Base):
    __tablename__ = "settlement_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    settlement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("settlements.id", ondelete="RESTRICT"), nullable=False
    )
    # payment_id is deliberately nullable to allow representing settlement items for missing payments
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )
    external_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0.00")
    )
    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0.00")
    )
    adjustment_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0.00")
    )
    net_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    source_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    item_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, name="metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    settlement: Mapped["Settlement"] = relationship("Settlement", back_populates="items")
    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="settlement_items")

    __table_args__ = (
        CheckConstraint("length(currency) = 3", name="ck_settlement_items_currency_length"),
        Index("ix_settlement_items_settlement_id", "settlement_id"),
        Index("ix_settlement_items_payment_id", "payment_id"),
        Index("ix_settlement_items_external_payment_id", "merchant_id", "external_payment_id"),
    )
