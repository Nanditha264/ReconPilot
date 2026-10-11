import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ActorType

if TYPE_CHECKING:
    from app.models.exception import ExceptionRecord
    from app.models.merchant import Merchant
    from app.models.reconciliation_run import ReconciliationRun


class AuditEvent(Base):
    """
    Append-only audit event trail tracking state changes, policy outcomes, and actor operations.
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    exception_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exceptions.id", ondelete="SET NULL"), nullable=True
    )
    reconciliation_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("reconciliation_runs.id", ondelete="SET NULL"), nullable=True
    )
    actor_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, name="actor_type_enum", native_enum=False),
        nullable=False,
    )
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, name="metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="audit_events")
    exception: Mapped["ExceptionRecord | None"] = relationship(
        "ExceptionRecord", back_populates="audit_events"
    )
    reconciliation_run: Mapped["ReconciliationRun | None"] = relationship(
        "ReconciliationRun", back_populates="audit_events"
    )

    __table_args__ = (
        Index("ix_audit_events_merchant_created", "merchant_id", "created_at"),
        Index("ix_audit_events_event_type", "event_type"),
        Index("ix_audit_events_exception_id", "exception_id"),
    )
