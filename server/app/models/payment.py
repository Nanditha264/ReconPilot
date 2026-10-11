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
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PaymentStatus

if TYPE_CHECKING:
    from app.models.adjustment import Adjustment
    from app.models.fee import Fee
    from app.models.merchant import Merchant
    from app.models.reconciliation_result import ReconciliationResult
    from app.models.refund import Refund
    from app.models.settlement_item import SettlementItem
    from app.models.source_integration import SourceIntegration


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    source_integration_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("source_integrations.id", ondelete="SET NULL"), nullable=True
    )
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    external_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum", native_enum=False),
        nullable=False,
        default=PaymentStatus.CAPTURED,
    )
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default="card")
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_metadata: Mapped[dict[str, Any] | None] = mapped_column(
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

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="payments")
    source_integration: Mapped["SourceIntegration | None"] = relationship(
        "SourceIntegration", back_populates="payments"
    )
    refunds: Mapped[list["Refund"]] = relationship("Refund", back_populates="payment")
    fees: Mapped[list["Fee"]] = relationship("Fee", back_populates="payment")
    adjustments: Mapped[list["Adjustment"]] = relationship("Adjustment", back_populates="payment")
    settlement_items: Mapped[list["SettlementItem"]] = relationship(
        "SettlementItem", back_populates="payment"
    )
    reconciliation_results: Mapped[list["ReconciliationResult"]] = relationship(
        "ReconciliationResult", back_populates="payment"
    )

    __table_args__ = (
        UniqueConstraint("merchant_id", "external_id", name="uq_payments_merchant_external_id"),
        CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
        CheckConstraint("length(currency) = 3", name="ck_payments_currency_length"),
        Index("ix_payments_merchant_status", "merchant_id", "status"),
        Index("ix_payments_merchant_source_created", "merchant_id", "source_created_at"),
        Index("ix_payments_external_order_id", "merchant_id", "external_order_id"),
    )
