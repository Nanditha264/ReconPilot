import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    Date,
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
from app.models.enums import SettlementStatus

if TYPE_CHECKING:
    from app.models.adjustment import Adjustment
    from app.models.merchant import Merchant
    from app.models.reconciliation_result import ReconciliationResult
    from app.models.settlement_item import SettlementItem
    from app.models.source_integration import SourceIntegration


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    source_integration_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("source_integrations.id", ondelete="SET NULL"), nullable=True
    )
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[SettlementStatus] = mapped_column(
        Enum(SettlementStatus, name="settlement_status_enum", native_enum=False),
        nullable=False,
        default=SettlementStatus.SETTLED,
    )
    initiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    settlement_metadata: Mapped[dict[str, Any] | None] = mapped_column(
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

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="settlements")
    source_integration: Mapped["SourceIntegration | None"] = relationship(
        "SourceIntegration", back_populates="settlements"
    )
    items: Mapped[list["SettlementItem"]] = relationship(
        "SettlementItem", back_populates="settlement", cascade="all, delete-orphan"
    )
    adjustments: Mapped[list["Adjustment"]] = relationship(
        "Adjustment", back_populates="settlement"
    )
    reconciliation_results: Mapped[list["ReconciliationResult"]] = relationship(
        "ReconciliationResult", back_populates="settlement"
    )

    __table_args__ = (
        UniqueConstraint("merchant_id", "external_id", name="uq_settlements_merchant_external_id"),
        CheckConstraint("length(currency) = 3", name="ck_settlements_currency_length"),
        Index("ix_settlements_merchant_date", "merchant_id", "settlement_date"),
        Index("ix_settlements_merchant_status", "merchant_id", "status"),
    )
