import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RunStatus, RunType

if TYPE_CHECKING:
    from app.models.audit_event import AuditEvent
    from app.models.merchant import Merchant
    from app.models.reconciliation_result import ReconciliationResult
    from app.models.source_integration import SourceIntegration


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    source_integration_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("source_integrations.id", ondelete="SET NULL"), nullable=True
    )
    run_type: Mapped[RunType] = mapped_column(
        Enum(RunType, name="run_type_enum", native_enum=False),
        nullable=False,
        default=RunType.MANUAL_TRIGGER,
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status_enum", native_enum=False),
        nullable=False,
        default=RunStatus.STARTED,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    matched_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unmatched_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exception_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_classified_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    review_required_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuration_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
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

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="reconciliation_runs")
    source_integration: Mapped["SourceIntegration | None"] = relationship(
        "SourceIntegration", back_populates="reconciliation_runs"
    )
    results: Mapped[list["ReconciliationResult"]] = relationship(
        "ReconciliationResult", back_populates="reconciliation_run", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="reconciliation_run"
    )

    __table_args__ = (
        Index("ix_reconciliation_runs_merchant_status", "merchant_id", "status"),
        Index("ix_reconciliation_runs_started_at", "started_at"),
    )
