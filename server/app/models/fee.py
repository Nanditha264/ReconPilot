import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import FeeStatus, FeeType

if TYPE_CHECKING:
    from app.models.merchant import Merchant
    from app.models.payment import Payment


class Fee(Base):
    __tablename__ = "fees"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id", ondelete="RESTRICT"), nullable=True
    )
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fee_type: Mapped[FeeType] = mapped_column(
        Enum(FeeType, name="fee_type_enum", native_enum=False),
        nullable=False,
        default=FeeType.MDR,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0.00")
    )
    status: Mapped[FeeStatus] = mapped_column(
        Enum(FeeStatus, name="fee_status_enum", native_enum=False),
        nullable=False,
        default=FeeStatus.ASSESSED,
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

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="fees")
    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="fees")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_fees_amount_non_negative"),
        CheckConstraint("tax_amount >= 0", name="ck_fees_tax_amount_non_negative"),
        CheckConstraint("length(currency) = 3", name="ck_fees_currency_length"),
        Index("ix_fees_merchant_payment", "merchant_id", "payment_id"),
        Index("ix_fees_fee_type", "fee_type"),
    )
