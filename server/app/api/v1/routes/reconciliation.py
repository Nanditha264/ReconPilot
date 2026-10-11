import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.reconciliation_result import ReconciliationResult
from app.models.reconciliation_run import ReconciliationRun
from app.models.user import User
from app.modules.reconciliation.schemas import (
    ReconciliationResultResponse,
    ReconciliationRunResponse,
    StartRunRequest,
)
from app.modules.reconciliation.service import run_reconciliation
from app.schemas.common import ApiResponse
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    paginate_query,
)

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation Engine"])


@router.post("/runs", response_model=ApiResponse[ReconciliationRunResponse])
def trigger_reconciliation_run(
    request: StartRunRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRole.ADMIN, UserRole.FINANCE_OPERATOR))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ReconciliationRunResponse]:
    """
    Triggers a new deterministic reconciliation run for the authenticated merchant.
    Calculates exact matches, discrepancy tolerances, and detects exceptions from raw financial records.
    """
    run_record = run_reconciliation(
        db=db,
        merchant_id=current_user.merchant_id,
        actor_id=str(current_user.id),
        run_type=request.run_type,
        tolerance=request.tolerance,
        settlement_delay_days=request.settlement_delay_days,
    )
    return ApiResponse.ok(ReconciliationRunResponse.model_validate(run_record))


@router.get("/runs", response_model=ApiResponse[PaginatedResponse[ReconciliationRunResponse]])
def list_reconciliation_runs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str | None = Query(default="started_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> ApiResponse[PaginatedResponse[ReconciliationRunResponse]]:
    """
    Returns paginated history of reconciliation runs scoped strictly to the authenticated merchant.
    """
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)  # type: ignore[arg-type]
    query = select(ReconciliationRun).where(
        ReconciliationRun.merchant_id == current_user.merchant_id
    )

    allowed_sort_fields = {
        "started_at": ReconciliationRun.started_at,
        "completed_at": ReconciliationRun.completed_at,
        "total_records": ReconciliationRun.total_records,
        "matched_records": ReconciliationRun.matched_records,
        "exception_records": ReconciliationRun.exception_records,
        "status": ReconciliationRun.status,
    }

    items, meta = paginate_query(
        db=db,
        query=query,
        params=params,
        allowed_sort_fields=allowed_sort_fields,
        default_sort_column=ReconciliationRun.started_at,
    )

    return ApiResponse.ok(
        PaginatedResponse(
            items=[ReconciliationRunResponse.model_validate(r) for r in items],
            meta=meta,
        )
    )


@router.get("/runs/{run_id}", response_model=ApiResponse[ReconciliationRunResponse])
def get_reconciliation_run_details(
    run_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ReconciliationRunResponse]:
    """
    Returns full run summary, counters, duration and configuration snapshot.
    Enforces merchant tenant isolation.
    """
    run_record = (
        db.query(ReconciliationRun)
        .filter(
            ReconciliationRun.id == run_id,
            ReconciliationRun.merchant_id == current_user.merchant_id,
        )
        .first()
    )

    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reconciliation run {run_id} not found.",
        )

    return ApiResponse.ok(ReconciliationRunResponse.model_validate(run_record))


@router.get(
    "/runs/{run_id}/results",
    response_model=ApiResponse[PaginatedResponse[ReconciliationResultResponse]],
)
def get_reconciliation_run_results(
    run_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str | None = Query(default="created_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    match_status: str | None = Query(default=None),
) -> ApiResponse[PaginatedResponse[ReconciliationResultResponse]]:
    """
    Returns paginated matching and calculation results generated by a specific reconciliation run.
    """
    # Verify run ownership
    run_record = (
        db.query(ReconciliationRun)
        .filter(
            ReconciliationRun.id == run_id,
            ReconciliationRun.merchant_id == current_user.merchant_id,
        )
        .first()
    )
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reconciliation run {run_id} not found.",
        )

    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)  # type: ignore[arg-type]
    query = select(ReconciliationResult).where(
        ReconciliationResult.run_id == run_id,
        ReconciliationResult.merchant_id == current_user.merchant_id,
    )
    if match_status:
        query = query.where(ReconciliationResult.match_status == match_status)

    allowed_sort_fields = {
        "created_at": ReconciliationResult.created_at,
        "match_status": ReconciliationResult.match_status,
        "match_type": ReconciliationResult.match_type,
        "difference": ReconciliationResult.difference,
        "expected_amount": ReconciliationResult.expected_amount,
    }

    items, meta = paginate_query(
        db=db,
        query=query,
        params=params,
        allowed_sort_fields=allowed_sort_fields,
        default_sort_column=ReconciliationResult.created_at,
    )

    return ApiResponse.ok(
        PaginatedResponse(
            items=[ReconciliationResultResponse.model_validate(r) for r in items],
            meta=meta,
        )
    )
