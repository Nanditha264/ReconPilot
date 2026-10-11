import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MerchantStatus

if TYPE_CHECKING:
    from app.models.adjustment import Adjustment
    from app.models.audit_event import AuditEvent
    from app.models.exception import ExceptionRecord
    from app.models.fee import Fee
    from app.models.payment import Payment
    from app.models.reconciliation_run import ReconciliationRun
    from app.models.refund import Refund
    from app.models.settlement import Settlement
    from app.models.source_integration import SourceIntegration
    from app.models.user import User


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    external_reference: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Kolkata")
    status: Mapped[MerchantStatus] = mapped_column(
        Enum(MerchantStatus, name="merchant_status_enum", native_enum=False),
        nullable=False,
        default=MerchantStatus.ACTIVE,
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

    # Relationships (financial history is protected - no cascade delete)
    source_integrations: Mapped[list["SourceIntegration"]] = relationship(
        "SourceIntegration", back_populates="merchant", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="merchant")
    refunds: Mapped[list["Refund"]] = relationship("Refund", back_populates="merchant")
    fees: Mapped[list["Fee"]] = relationship("Fee", back_populates="merchant")
    settlements: Mapped[list["Settlement"]] = relationship("Settlement", back_populates="merchant")
    adjustments: Mapped[list["Adjustment"]] = relationship("Adjustment", back_populates="merchant")
    reconciliation_runs: Mapped[list["ReconciliationRun"]] = relationship(
        "ReconciliationRun", back_populates="merchant"
    )
    exceptions: Mapped[list["ExceptionRecord"]] = relationship(
        "ExceptionRecord", back_populates="merchant"
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship("AuditEvent", back_populates="merchant")
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="merchant", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("length(currency) = 3", name="ck_merchant_currency_length"),
        Index("ix_merchants_status", "status"),
    )
