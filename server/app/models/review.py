import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ExceptionStatus, ReviewDecision

if TYPE_CHECKING:
    from app.models.exception import ExceptionRecord


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exception_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exceptions.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[ReviewDecision] = mapped_column(
        Enum(ReviewDecision, name="review_decision_enum", native_enum=False),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[ExceptionStatus] = mapped_column(
        Enum(ExceptionStatus, name="review_prev_status_enum", native_enum=False),
        nullable=False,
    )
    new_status: Mapped[ExceptionStatus] = mapped_column(
        Enum(ExceptionStatus, name="review_new_status_enum", native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    exception: Mapped["ExceptionRecord"] = relationship("ExceptionRecord", back_populates="reviews")

    __table_args__ = (
        Index("ix_reviews_exception_id", "exception_id"),
        Index("ix_reviews_reviewer_id", "reviewer_id"),
    )
