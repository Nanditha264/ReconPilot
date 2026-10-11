import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    from app.models.exception import ExceptionRecord
    from app.models.merchant import Merchant
    from app.models.resolution_proposal import ResolutionProposal
    from app.models.user import User


class ResolutionHistory(Base):
    """
    Append-only audit trail tracking every lifecycle transition, proposal state change,
    and operator decision for an exception.
    """

    __tablename__ = "resolution_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    exception_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exceptions.id", ondelete="CASCADE"), nullable=False
    )
    proposal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resolution_proposals.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, name="metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship("Merchant")
    exception: Mapped["ExceptionRecord"] = relationship(
        "ExceptionRecord", back_populates="resolution_history"
    )
    proposal: Mapped["ResolutionProposal | None"] = relationship("ResolutionProposal")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_resolution_history_merchant_id", "merchant_id"),
        Index("ix_resolution_history_exception_id", "exception_id"),
        Index("ix_resolution_history_created_at", "created_at"),
        Index("ix_resolution_history_event_type", "event_type"),
    )
