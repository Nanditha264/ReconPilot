import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import ExceptionSeverity, ExceptionStatus, ExceptionType, ResolutionCategory


class CurrencyExposure(BaseModel):
    """Financial exposure aggregated by individual currency."""

    currency: str
    total_exposure: Decimal
    exception_count: int


class AIInvestigationOverview(BaseModel):
    """Aggregate metrics of AI investigation reports."""

    completed_count: int = 0
    pending_count: int = 0
    failed_count: int = 0
    unavailable_count: int = 0
    requires_human_review_count: int = 0


class DashboardOverviewResponse(BaseModel):
    """Executive KPI response scoped to the authenticated merchant."""

    merchant_id: uuid.UUID
    total_payments_processed: int
    matched_records: int
    unmatched_records: int
    exception_records: int
    match_rate_percentage: float
    total_exposure_by_currency: list[CurrencyExposure]
    pending_approvals_count: int
    exceptions_awaiting_review: int
    resolved_exceptions_count: int
    ai_investigations: AIInvestigationOverview
    last_reconciliation_at: datetime | None = None


class ExceptionTypeBreakdown(BaseModel):
    """Distribution of exceptions by type."""

    exception_type: str
    count: int
    total_exposure: Decimal
    currency: str


class ResolutionStatusBreakdown(BaseModel):
    """Distribution of exceptions across the resolution lifecycle."""

    status: str
    count: int


class SeverityBreakdown(BaseModel):
    """Distribution of exceptions by severity."""

    severity: str
    count: int


class ReconciliationHealthResponse(BaseModel):
    """Detailed reconciliation health distributions."""

    merchant_id: uuid.UUID
    match_distribution: dict[str, int]
    exceptions_by_type: list[ExceptionTypeBreakdown]
    exposure_by_currency: list[CurrencyExposure]
    resolution_status_distribution: list[ResolutionStatusBreakdown]
    severity_distribution: list[SeverityBreakdown]


class ReconciliationRunTrendItem(BaseModel):
    """Historical reconciliation run trend entry."""

    run_id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None
    status: str
    total_records: int
    matched_records: int
    unmatched_records: int
    exception_records: int
    match_rate_percentage: float


class ExceptionTrendItem(BaseModel):
    """Time-series aggregation of detected exceptions."""

    date: str
    count: int
    total_exposure: Decimal
    currency: str


class DashboardTrendsResponse(BaseModel):
    """Reconciliation runs history and exception time-series trends."""

    merchant_id: uuid.UUID
    runs_history: list[ReconciliationRunTrendItem]
    exception_trends: list[ExceptionTrendItem]


class PendingApprovalItem(BaseModel):
    """Resolution proposal pending human reviewer approval."""

    proposal_id: uuid.UUID
    exception_id: uuid.UUID
    exception_type: ExceptionType
    severity: ExceptionSeverity
    proposal_category: ResolutionCategory
    proposed_action: str
    explanation: str
    financial_impact: Decimal
    currency: str
    created_by_user_id: uuid.UUID
    created_by_user_name: str | None
    submitted_at: datetime
    is_current_user_author: bool
    can_current_user_approve: bool


class OperationsQueueItem(BaseModel):
    """Summary item for the exception operations queue."""

    exception_id: uuid.UUID
    exception_type: ExceptionType
    severity: ExceptionSeverity
    status: ExceptionStatus
    resolution_status: str
    financial_impact: Decimal
    currency: str
    first_detected_at: datetime
    age_days: int
    evidence_count: int
    evidence_strength: str | None
    ai_investigation_status: str | None
    ai_requires_human_review: bool | None
    has_pending_proposal: bool
    active_proposal_id: uuid.UUID | None
    active_proposal_category: str | None


class OperationsQueueResponse(BaseModel):
    """Paginated operations queue response."""

    items: list[OperationsQueueItem]
    total: int
    page: int
    page_size: int
    total_pages: int
