import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SourceProvider, SyncStatus

if TYPE_CHECKING:
    from app.models.merchant import Merchant
    from app.models.payment import Payment
    from app.models.reconciliation_run import ReconciliationRun
    from app.models.settlement import Settlement


class SourceIntegration(Base):
    __tablename__ = "source_integrations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False
    )
    provider: Mapped[SourceProvider] = mapped_column(
        Enum(SourceProvider, name="source_provider_enum", native_enum=False),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    environment: Mapped[str] = mapped_column(String(50), nullable=False, default="sandbox")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus, name="sync_status_enum", native_enum=False),
        nullable=False,
        default=SyncStatus.IDLE,
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

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="source_integrations")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="source_integration")
    settlements: Mapped[list["Settlement"]] = relationship(
        "Settlement", back_populates="source_integration"
    )
    reconciliation_runs: Mapped[list["ReconciliationRun"]] = relationship(
        "ReconciliationRun", back_populates="source_integration"
    )

    __table_args__ = (Index("ix_source_integrations_merchant_provider", "merchant_id", "provider"),)
