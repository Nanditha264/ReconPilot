import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AdjustmentStatus, AdjustmentType

if TYPE_CHECKING:
    from app.models.merchant import Merchant
    from app.models.payment import Payment
    from app.models.settlement import Settlement


class Adjustment(Base):
    """
    Financial Adjustment model adhering to the signed convention:
    - Positive adjustment: increases expected settlement to merchant.
    - Negative adjustment: decreases expected settlement to merchant.
    expected_settlement = payment_amount - refunds - fees + signed_adjustments
    """

    __tablename__ = "adjustments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )
    settlement_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("settlements.id", ondelete="SET NULL"), nullable=True
    )
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Amount is signed - can be positive or negative
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    adjustment_type: Mapped[AdjustmentType] = mapped_column(
        Enum(AdjustmentType, name="adjustment_type_enum", native_enum=False),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AdjustmentStatus] = mapped_column(
        Enum(AdjustmentStatus, name="adjustment_status_enum", native_enum=False),
        nullable=False,
        default=AdjustmentStatus.APPLIED,
    )
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    adjustment_metadata: Mapped[dict[str, Any] | None] = mapped_column(
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

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="adjustments")
    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="adjustments")
    settlement: Mapped["Settlement | None"] = relationship(
        "Settlement", back_populates="adjustments"
    )

    __table_args__ = (
        CheckConstraint("length(currency) = 3", name="ck_adjustments_currency_length"),
        Index("ix_adjustments_merchant_type", "merchant_id", "adjustment_type"),
        Index("ix_adjustments_payment_id", "payment_id"),
        Index("ix_adjustments_settlement_id", "settlement_id"),
    )
