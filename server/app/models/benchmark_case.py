import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ExceptionType, MatchStatus


# Ground-truth evaluation benchmarks must be independent of runtime AI predictions.
class BenchmarkCase(Base):
    """
    Ground-truth test case definition for evaluating deterministic reconciliation and AI reasoners.
    Expected labels are curated human truths, never derived from model output.
    """

    __tablename__ = "benchmark_cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    source_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="benchmark_match_status_enum", native_enum=False),
        nullable=False,
    )
    expected_exception_type: Mapped[ExceptionType | None] = mapped_column(
        Enum(ExceptionType, name="benchmark_exception_type_enum", native_enum=False),
        nullable=True,
    )
    expected_root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_financial_impact: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0.00")
    )
    expected_policy_outcome: Mapped[str] = mapped_column(
        String(50), nullable=False, default="AUTO_RESOLVE"
    )
    case_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, name="metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_benchmark_cases_dataset_scenario", "dataset_version", "scenario_id"),
        Index("ix_benchmark_cases_expected_type", "expected_exception_type"),
    )
