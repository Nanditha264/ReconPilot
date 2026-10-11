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
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ExceptionSeverity, ExceptionStatus, ExceptionType

if TYPE_CHECKING:
    from app.models.ai_investigation import AIInvestigation
    from app.models.audit_event import AuditEvent
    from app.models.evidence import Evidence
    from app.models.investigation_report import InvestigationReport
    from app.models.merchant import Merchant
    from app.models.reconciliation_result import ReconciliationResult
    from app.models.resolution_history import ResolutionHistory
    from app.models.resolution_proposal import ResolutionProposal
    from app.models.review import Review


class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    reconciliation_result_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reconciliation_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    exception_type: Mapped[ExceptionType] = mapped_column(
        Enum(ExceptionType, name="exception_type_enum", native_enum=False),
        nullable=False,
    )
    severity: Mapped[ExceptionSeverity] = mapped_column(
        Enum(ExceptionSeverity, name="exception_severity_enum", native_enum=False),
        nullable=False,
        default=ExceptionSeverity.MEDIUM,
    )
    status: Mapped[ExceptionStatus] = mapped_column(
        Enum(ExceptionStatus, name="exception_status_enum", native_enum=False),
        nullable=False,
        default=ExceptionStatus.OPEN,
    )
    resolution_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OPEN",
    )
    financial_impact: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="exceptions")
    reconciliation_result: Mapped["ReconciliationResult"] = relationship(
        "ReconciliationResult", back_populates="exception"
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="exception", cascade="all, delete-orphan"
    )
    ai_investigations: Mapped[list["AIInvestigation"]] = relationship(
        "AIInvestigation", back_populates="exception", cascade="all, delete-orphan"
    )
    investigation_reports: Mapped[list["InvestigationReport"]] = relationship(
        "InvestigationReport", back_populates="exception", cascade="all, delete-orphan"
    )
    resolution_proposals: Mapped[list["ResolutionProposal"]] = relationship(
        "ResolutionProposal", back_populates="exception", cascade="all, delete-orphan"
    )
    resolution_history: Mapped[list["ResolutionHistory"]] = relationship(
        "ResolutionHistory", back_populates="exception", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="exception", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="exception"
    )

    __table_args__ = (
        CheckConstraint("length(currency) = 3", name="ck_exceptions_currency_length"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_exceptions_confidence_range",
        ),
        Index("ix_exceptions_merchant_status", "merchant_id", "status"),
        Index("ix_exceptions_type_severity", "exception_type", "severity"),
        Index("ix_exceptions_resolution_status", "resolution_status"),
    )
