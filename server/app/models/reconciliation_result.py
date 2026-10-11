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
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MatchStatus, MatchType

if TYPE_CHECKING:
    from app.models.exception import ExceptionRecord
    from app.models.payment import Payment
    from app.models.reconciliation_run import ReconciliationRun
    from app.models.settlement import Settlement


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("reconciliation_runs.id", ondelete="CASCADE"), nullable=False
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    # payment_id is nullable for unmatched settlements
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )
    # settlement_id is nullable when no settlement exists for a payment
    settlement_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("settlements.id", ondelete="SET NULL"), nullable=True
    )
    match_type: Mapped[MatchType] = mapped_column(
        Enum(MatchType, name="match_type_enum", native_enum=False),
        nullable=False,
        default=MatchType.EXACT_2_WAY,
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="match_status_enum", native_enum=False),
        nullable=False,
    )
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    difference: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0.00")
    )
    tolerance: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0.00")
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("1.0000")
    )
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    matching_fields: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    reconciliation_run: Mapped["ReconciliationRun"] = relationship(
        "ReconciliationRun", back_populates="results"
    )
    payment: Mapped["Payment | None"] = relationship(
        "Payment", back_populates="reconciliation_results"
    )
    settlement: Mapped["Settlement | None"] = relationship(
        "Settlement", back_populates="reconciliation_results"
    )
    exception: Mapped["ExceptionRecord | None"] = relationship(
        "ExceptionRecord", back_populates="reconciliation_result", uselist=False
    )

    __table_args__ = (
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_reconciliation_results_confidence_range",
        ),
        Index("ix_reconciliation_results_run_status", "run_id", "match_status"),
        Index("ix_reconciliation_results_payment_id", "payment_id"),
        Index("ix_reconciliation_results_settlement_id", "settlement_id"),
    )
