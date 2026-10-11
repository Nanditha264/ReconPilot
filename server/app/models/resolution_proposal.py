import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ProposalStatus, ResolutionCategory

if TYPE_CHECKING:
    from app.models.exception import ExceptionRecord
    from app.models.investigation_report import InvestigationReport
    from app.models.merchant import Merchant
    from app.models.user import User


class ResolutionProposal(Base):
    """
    Represents an operator-submitted resolution proposal for an exception,
    subject to reviewer approval and separation of duties.
    """

    __tablename__ = "resolution_proposals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    exception_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exceptions.id", ondelete="CASCADE"), nullable=False
    )
    investigation_report_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigation_reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ResolutionCategory.OTHER.value
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProposalStatus.DRAFT.value
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_action: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_evidence_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    decision_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decision_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    merchant: Mapped["Merchant"] = relationship("Merchant")
    exception: Mapped["ExceptionRecord"] = relationship(
        "ExceptionRecord", back_populates="resolution_proposals"
    )
    investigation_report: Mapped["InvestigationReport | None"] = relationship("InvestigationReport")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    decision_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[decision_by_user_id]
    )

    __table_args__ = (
        Index("ix_resolution_proposals_merchant_id", "merchant_id"),
        Index("ix_resolution_proposals_exception_id", "exception_id"),
        Index("ix_resolution_proposals_status", "status"),
        Index("ix_resolution_proposals_created_at", "created_at"),
    )
