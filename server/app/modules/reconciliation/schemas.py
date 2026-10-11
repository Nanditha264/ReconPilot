import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    MatchStatus,
    MatchType,
    RunStatus,
    RunType,
)


class StartRunRequest(BaseModel):
    run_type: RunType = Field(default=RunType.MANUAL_TRIGGER, description="Execution trigger type")
    tolerance: Decimal | None = Field(
        default=None, ge=Decimal("0.00"), description="Optional override tolerance"
    )
    settlement_delay_days: int | None = Field(
        default=None, ge=1, le=30, description="Optional override delay window"
    )


class ReconciliationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    run_type: RunType
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None = None
    total_records: int
    matched_records: int
    unmatched_records: int
    exception_records: int
    auto_classified_records: int
    review_required_records: int
    processing_duration_ms: int | None = None
    error_summary: str | None = None
    configuration_snapshot: dict[str, Any] | None = None
    created_at: datetime


class ReconciliationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    merchant_id: uuid.UUID
    payment_id: uuid.UUID | None = None
    settlement_id: uuid.UUID | None = None
    match_type: MatchType
    match_status: MatchStatus
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    tolerance: Decimal
    confidence: Decimal
    explanation: str | None = None
    matching_fields: dict[str, Any] | None = None
    created_at: datetime


class IngestionSummaryResponse(BaseModel):
    total_records_processed: int
    inserted_payments: int
    inserted_settlements: int
    inserted_items: int
    inserted_refunds: int
    inserted_fees: int
    inserted_adjustments: int
    skipped_records: int
    duration_ms: int
