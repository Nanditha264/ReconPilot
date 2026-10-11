import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.enums import ExceptionSeverity, ExceptionStatus, ExceptionType
from app.models.exception import ExceptionRecord
from app.models.reconciliation_result import ReconciliationResult
from app.models.user import User
from app.modules.evidence.schemas import (
    ExceptionEvidenceResponse,
    FinancialEvidenceSummary,
)
from app.modules.evidence.service import EvidenceCollector, EvidenceCorrelator
from app.modules.investigation.schemas import (
    InvestigationResponse,
    StartInvestigationRequest,
)
from app.modules.investigation.service import InvestigationService
from app.modules.reconciliation.schemas import ReconciliationResultResponse
from app.modules.resolution.schemas import (
    CreateProposalRequest,
    DecisionRequest,
    ProposalResponse,
    ReopenExceptionRequest,
    ResolutionHistoryItem,
    ResolutionSummaryResponse,
    ResolveExceptionRequest,
)
from app.modules.resolution.service import ResolutionService
from app.schemas.common import ApiResponse
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    paginate_query,
)

router = APIRouter(prefix="/exceptions", tags=["Exception Operations"])


class ExceptionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    reconciliation_result_id: uuid.UUID
    exception_type: ExceptionType
    severity: ExceptionSeverity
    status: ExceptionStatus
    financial_impact: Decimal
    currency: str
    description: str
    created_at: datetime


class ExceptionDetailResponse(BaseModel):
    exception: ExceptionSummaryResponse
    reconciliation_result: ReconciliationResultResponse | None = None


@router.get("", response_model=ApiResponse[PaginatedResponse[ExceptionSummaryResponse]])
def list_exceptions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str | None = Query(default="created_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    exception_type: ExceptionType | None = Query(default=None),
    status: ExceptionStatus | None = Query(default=None),
    severity: ExceptionSeverity | None = Query(default=None),
    search: str | None = Query(default=None),
) -> ApiResponse[PaginatedResponse[ExceptionSummaryResponse]]:
    """
    Returns paginated list of exceptions scoped to the authenticated merchant with filtering and search.
    """
    params = PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,  # type: ignore[arg-type]
    )

    query = select(ExceptionRecord).where(ExceptionRecord.merchant_id == current_user.merchant_id)
    if exception_type:
        query = query.where(ExceptionRecord.exception_type == exception_type)
    if status:
        query = query.where(ExceptionRecord.status == status)
    if severity:
        query = query.where(ExceptionRecord.severity == severity)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(ExceptionRecord.description.ilike(search_filter))

    allowed_sort_fields = {
        "created_at": ExceptionRecord.created_at,
        "financial_impact": ExceptionRecord.financial_impact,
        "severity": ExceptionRecord.severity,
        "status": ExceptionRecord.status,
        "exception_type": ExceptionRecord.exception_type,
    }

    items, meta = paginate_query(
        db=db,
        query=query,
        params=params,
        allowed_sort_fields=allowed_sort_fields,
        default_sort_column=ExceptionRecord.created_at,
    )

    return ApiResponse.ok(
        PaginatedResponse(
            items=[ExceptionSummaryResponse.model_validate(ex) for ex in items],
            meta=meta,
        )
    )


@router.get("/{exception_id}", response_model=ApiResponse[ExceptionDetailResponse])
def get_exception_details(
    exception_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ExceptionDetailResponse]:
    """
    Returns full exception details and associated reconciliation result calculation.
    Enforces merchant tenant isolation.
    """
    exc = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.id == exception_id,
            ExceptionRecord.merchant_id == current_user.merchant_id,
        )
        .first()
    )

    if not exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception record {exception_id} not found.",
        )

    res = (
        db.query(ReconciliationResult)
        .filter(ReconciliationResult.id == exc.reconciliation_result_id)
        .first()
    )

    return ApiResponse.ok(
        ExceptionDetailResponse(
            exception=ExceptionSummaryResponse.model_validate(exc),
            reconciliation_result=ReconciliationResultResponse.model_validate(res) if res else None,
        )
    )


@router.get("/{exception_id}/evidence", response_model=ApiResponse[ExceptionEvidenceResponse])
def get_exception_evidence(
    exception_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ExceptionEvidenceResponse]:
    """
    Returns structured financial evidence and correlation dossier for a single exception.
    Enforces tenant isolation and returns 404 for inaccessible or non-existent records.
    """
    collector = EvidenceCollector(db=db, merchant_id=current_user.merchant_id)
    raw_evidence = collector.collect(exception_id=exception_id)

    if not raw_evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception record {exception_id} not found.",
        )

    evidence_response = EvidenceCorrelator.correlate(raw_evidence)
    return ApiResponse.ok(evidence_response)


@router.get(
    "/{exception_id}/evidence/summary",
    response_model=ApiResponse[FinancialEvidenceSummary],
)
def get_exception_evidence_summary(
    exception_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[FinancialEvidenceSummary]:
    """
    Returns concise financial discrepancy summary, supported findings, and evidence limitations.
    Enforces tenant isolation and returns 404 for inaccessible records.
    """
    collector = EvidenceCollector(db=db, merchant_id=current_user.merchant_id)
    raw_evidence = collector.collect(exception_id=exception_id)

    if not raw_evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception record {exception_id} not found.",
        )

    evidence_response = EvidenceCorrelator.correlate(raw_evidence)
    return ApiResponse.ok(evidence_response.summary)


@router.post(
    "/{exception_id}/investigations",
    response_model=ApiResponse[InvestigationResponse],
)
async def start_exception_investigation(
    exception_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    body: StartInvestigationRequest | None = None,
) -> ApiResponse[InvestigationResponse]:
    """
    Starts or retrieves an evidence-grounded AI investigation for an exception.
    Enforces tenant isolation and policy gates. Returns 404 for inaccessible records.
    """
    service = InvestigationService(db=db, merchant_id=current_user.merchant_id)
    investigation = await service.run_investigation(exception_id=exception_id, request=body)
    return ApiResponse.ok(investigation)


@router.get(
    "/{exception_id}/investigations/latest",
    response_model=ApiResponse[InvestigationResponse],
)
def get_latest_exception_investigation(
    exception_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[InvestigationResponse]:
    """
    Retrieves the latest investigation report for an exception.
    Enforces tenant isolation. Returns 404 if no investigation exists.
    """
    service = InvestigationService(db=db, merchant_id=current_user.merchant_id)
    investigation = service.get_latest_investigation(exception_id=exception_id)

    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No investigation report found for exception {exception_id}.",
        )

    return ApiResponse.ok(investigation)


# =============================================================================
# Phase 07: Resolution & Human Approval Endpoints
# =============================================================================


@router.get(
    "/{exception_id}/resolution",
    response_model=ApiResponse[ResolutionSummaryResponse],
)
def get_exception_resolution_summary(
    exception_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ResolutionSummaryResponse]:
    """
    Retrieves the current resolution status, active proposal, and operator permissions.
    Enforces tenant isolation.
    """
    service = ResolutionService(db=db, merchant_id=current_user.merchant_id)
    summary = service.get_resolution_summary(exception_id=exception_id, current_user=current_user)
    return ApiResponse.ok(summary)


@router.get(
    "/{exception_id}/resolution/history",
    response_model=ApiResponse[list[ResolutionHistoryItem]],
)
def get_exception_resolution_history(
    exception_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[list[ResolutionHistoryItem]]:
    """
    Retrieves the ordered immutable history of all resolution events for this exception.
    """
    service = ResolutionService(db=db, merchant_id=current_user.merchant_id)
    history = service.get_history(exception_id=exception_id)
    return ApiResponse.ok(history)


@router.post(
    "/{exception_id}/resolution/proposals",
    response_model=ApiResponse[ProposalResponse],
)
def create_resolution_proposal(
    exception_id: uuid.UUID,
    body: CreateProposalRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProposalResponse]:
    """
    Creates a new resolution proposal. Validates all cited evidence against the dossier.
    """
    service = ResolutionService(db=db, merchant_id=current_user.merchant_id)
    proposal = service.create_proposal(
        exception_id=exception_id, request=body, current_user=current_user
    )
    return ApiResponse.ok(proposal)


@router.post(
    "/{exception_id}/resolution/proposals/{proposal_id}/submit",
    response_model=ApiResponse[ProposalResponse],
)
def submit_resolution_proposal(
    exception_id: uuid.UUID,
    proposal_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProposalResponse]:
    """
    Submits a DRAFT proposal for reviewer approval.
    """
    service = ResolutionService(db=db, merchant_id=current_user.merchant_id)
    proposal = service.submit_proposal(
        exception_id=exception_id, proposal_id=proposal_id, current_user=current_user
    )
    return ApiResponse.ok(proposal)


@router.post(
    "/{exception_id}/resolution/proposals/{proposal_id}/approve",
    response_model=ApiResponse[ProposalResponse],
)
def approve_resolution_proposal(
    exception_id: uuid.UUID,
    proposal_id: uuid.UUID,
    body: DecisionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProposalResponse]:
    """
    Approves a resolution proposal. Enforces separation of duties and reviewer role.
    """
    service = ResolutionService(db=db, merchant_id=current_user.merchant_id)
    proposal = service.approve_proposal(
        exception_id=exception_id,
        proposal_id=proposal_id,
        request=body,
        current_user=current_user,
    )
    return ApiResponse.ok(proposal)


@router.post(
    "/{exception_id}/resolution/proposals/{proposal_id}/reject",
    response_model=ApiResponse[ProposalResponse],
)
def reject_resolution_proposal(
    exception_id: uuid.UUID,
    proposal_id: uuid.UUID,
    body: DecisionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProposalResponse]:
    """
    Rejects a resolution proposal with mandatory explanation reason.
    """
    service = ResolutionService(db=db, merchant_id=current_user.merchant_id)
    proposal = service.reject_proposal(
        exception_id=exception_id,
        proposal_id=proposal_id,
        request=body,
        current_user=current_user,
    )
    return ApiResponse.ok(proposal)


@router.post(
    "/{exception_id}/resolution/resolve",
    response_model=ApiResponse[ResolutionSummaryResponse],
)
def resolve_exception(
    exception_id: uuid.UUID,
    body: ResolveExceptionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ResolutionSummaryResponse]:
    """
    Explicitly marks the exception as RESOLVED following an approved proposal.
    """
    service = ResolutionService(db=db, merchant_id=current_user.merchant_id)
    summary = service.resolve_exception(
        exception_id=exception_id, request=body, current_user=current_user
    )
    return ApiResponse.ok(summary)


@router.post(
    "/{exception_id}/resolution/reopen",
    response_model=ApiResponse[ResolutionSummaryResponse],
)
def reopen_exception(
    exception_id: uuid.UUID,
    body: ReopenExceptionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ResolutionSummaryResponse]:
    """
    Reopens a previously resolved exception. Requires mandatory business justification.
    """
    service = ResolutionService(db=db, merchant_id=current_user.merchant_id)
    summary = service.reopen_exception(
        exception_id=exception_id, request=body, current_user=current_user
    )
    return ApiResponse.ok(summary)
