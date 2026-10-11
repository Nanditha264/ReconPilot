from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.modules.dashboard.schemas import (
    DashboardOverviewResponse,
    DashboardTrendsResponse,
    OperationsQueueResponse,
    PendingApprovalItem,
    ReconciliationHealthResponse,
)
from app.modules.dashboard.service import DashboardService
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/dashboard", tags=["Finance Operations Dashboard"])


@router.get("/overview", response_model=ApiResponse[DashboardOverviewResponse])
def get_dashboard_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[DashboardOverviewResponse]:
    """
    Returns executive-level reconciliation KPIs, financial exposure totals,
    and investigation/approval metrics scoped to the authenticated merchant.
    """
    service = DashboardService(db=db, merchant_id=current_user.merchant_id)
    overview = service.get_overview()
    return ApiResponse.ok(overview)


@router.get("/reconciliation-health", response_model=ApiResponse[ReconciliationHealthResponse])
def get_reconciliation_health(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ReconciliationHealthResponse]:
    """
    Returns categorical distributions of match statuses, exception types,
    currency exposure, severity, and resolution progress.
    """
    service = DashboardService(db=db, merchant_id=current_user.merchant_id)
    health = service.get_reconciliation_health()
    return ApiResponse.ok(health)


@router.get("/exception-trends", response_model=ApiResponse[DashboardTrendsResponse])
def get_exception_trends(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[DashboardTrendsResponse]:
    """
    Returns historical reconciliation runs activity and daily detected exception trends.
    """
    service = DashboardService(db=db, merchant_id=current_user.merchant_id)
    trends = service.get_exception_trends()
    return ApiResponse.ok(trends)


@router.get("/pending-approvals", response_model=ApiResponse[list[PendingApprovalItem]])
def get_pending_approvals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[list[PendingApprovalItem]]:
    """
    Returns resolution proposals currently awaiting reviewer approval.
    Computes separation-of-duties and reviewer authorization for the requesting user.
    """
    service = DashboardService(db=db, merchant_id=current_user.merchant_id)
    proposals = service.get_pending_approvals(current_user=current_user)
    return ApiResponse.ok(proposals)


@router.get("/operations-queue", response_model=ApiResponse[OperationsQueueResponse])
def get_operations_queue(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Records per page"),
    status: str | None = Query(default=None, description="Filter by status or resolution status"),
    exception_type: str | None = Query(default=None, description="Filter by exception type"),
    currency: str | None = Query(default=None, description="Filter by currency code"),
    min_impact: Decimal | None = Query(default=None, description="Minimum financial impact"),
    max_impact: Decimal | None = Query(default=None, description="Maximum financial impact"),
    search: str | None = Query(default=None, description="Search by ID or description"),
    sort_by: str = Query(default="detected_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", description="Sort direction (asc/desc)"),
) -> ApiResponse[OperationsQueueResponse]:
    """
    Returns a paginated and filterable queue of exceptions for operational triage.
    """
    service = DashboardService(db=db, merchant_id=current_user.merchant_id)
    queue = service.get_operations_queue(
        page=page,
        page_size=page_size,
        status=status,
        exception_type=exception_type,
        currency=currency,
        min_impact=min_impact,
        max_impact=max_impact,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ApiResponse.ok(queue)
