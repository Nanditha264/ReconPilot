import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    EvidenceCategory,
    EvidenceStrength,
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    MatchStatus,
)


class ReconciliationContext(BaseModel):
    """Context extracted from the authoritative reconciliation result."""

    model_config = ConfigDict(from_attributes=True)

    result_id: uuid.UUID
    run_id: uuid.UUID
    match_status: MatchStatus
    exception_type: ExceptionType
    severity: ExceptionSeverity
    exception_status: ExceptionStatus
    expected_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    currency: str
    tolerance: Decimal
    explanation: str | None = None
    created_at: datetime


class EvidenceItem(BaseModel):
    """A structured piece of financial evidence linked to authoritative records."""

    model_config = ConfigDict(from_attributes=True)

    evidence_id: str = Field(description="Stable evidence reference identifier")
    category: EvidenceCategory
    source_type: str = Field(
        description="Name of the underlying entity, e.g. payment, settlement_item"
    )
    source_record_id: str | None = Field(
        default=None, description="UUID of the underlying record if existing"
    )
    strength: EvidenceStrength
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Concrete attributes of the record"
    )
    limitations: list[str] = Field(
        default_factory=list, description="Caveats, missing fields or notes"
    )
    timestamp: datetime | None = Field(
        default=None, description="Event or record creation timestamp"
    )


class RelatedRecordsSummary(BaseModel):
    """High-level counts and identifiers of discovered related financial records."""

    payment_ids: list[str] = Field(default_factory=list)
    settlement_item_ids: list[str] = Field(default_factory=list)
    settlement_ids: list[str] = Field(default_factory=list)
    refund_ids: list[str] = Field(default_factory=list)
    fee_ids: list[str] = Field(default_factory=list)
    adjustment_ids: list[str] = Field(default_factory=list)
    audit_event_ids: list[str] = Field(default_factory=list)


class FinancialEvidenceSummary(BaseModel):
    """Deterministic financial breakdown and operator-facing findings."""

    model_config = ConfigDict(from_attributes=True)

    observed_discrepancy: str
    expected_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    currency: str
    overall_strength: EvidenceStrength
    cause_established: bool
    supported_findings: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class ExceptionEvidenceResponse(BaseModel):
    """Complete structured evidence dossier for a single reconciliation exception."""

    model_config = ConfigDict(from_attributes=True)

    exception_id: uuid.UUID
    merchant_id: uuid.UUID
    reconciliation: ReconciliationContext
    evidence_items: list[EvidenceItem]
    related_records: RelatedRecordsSummary
    summary: FinancialEvidenceSummary
