import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EvidenceType

if TYPE_CHECKING:
    from app.models.exception import ExceptionRecord


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exception_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exceptions.id", ondelete="CASCADE"), nullable=False
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type_enum", native_enum=False),
        nullable=False,
    )
    source_table: Mapped[str] = mapped_column(String(100), nullable=False)
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    exception: Mapped["ExceptionRecord"] = relationship(
        "ExceptionRecord", back_populates="evidence_items"
    )

    __table_args__ = (
        Index("ix_evidence_exception_id", "exception_id"),
        Index("ix_evidence_source_record", "source_table", "source_record_id"),
    )
