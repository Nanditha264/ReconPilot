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
from app.models.enums import PaymentStatus
from app.models.fee import Fee
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.settlement_item import SettlementItem
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    paginate_query,
)

router = APIRouter(prefix="/transactions", tags=["Financial Transactions"])


class TransactionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    external_id: str
    external_order_id: str | None = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: str
    captured_at: datetime | None = None
    source_created_at: datetime


class FeeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    fee_type: str
    amount: Decimal
    tax_amount: Decimal
    status: str


class RefundSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    external_id: str
    amount: Decimal
    status: str
    processed_at: datetime


class SettlementItemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    settlement_id: uuid.UUID
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    source_created_at: datetime


class TransactionDetailResponse(BaseModel):
    payment: TransactionSummaryResponse
    fees: list[FeeSummary]
    refunds: list[RefundSummary]
    settlement_items: list[SettlementItemSummary]


@router.get("", response_model=ApiResponse[PaginatedResponse[TransactionSummaryResponse]])
def list_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str | None = Query(default="source_created_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    status: PaymentStatus | None = Query(default=None),
    search: str | None = Query(default=None),
) -> ApiResponse[PaginatedResponse[TransactionSummaryResponse]]:
    """
    Returns paginated list of persisted payments for the authenticated merchant.
    """
    params = PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,  # type: ignore[arg-type]
    )

    query = select(Payment).where(Payment.merchant_id == current_user.merchant_id)
    if status:
        query = query.where(Payment.status == status)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(
            Payment.external_id.ilike(search_filter)
            | Payment.external_order_id.ilike(search_filter)
        )

    allowed_sort_fields = {
        "source_created_at": Payment.source_created_at,
        "amount": Payment.amount,
        "status": Payment.status,
        "external_id": Payment.external_id,
    }

    items, meta = paginate_query(
        db=db,
        query=query,
        params=params,
        allowed_sort_fields=allowed_sort_fields,
        default_sort_column=Payment.source_created_at,
    )

    return ApiResponse.ok(
        PaginatedResponse(
            items=[TransactionSummaryResponse.model_validate(p) for p in items],
            meta=meta,
        )
    )


@router.get("/{transaction_id}", response_model=ApiResponse[TransactionDetailResponse])
def get_transaction_details(
    transaction_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[TransactionDetailResponse]:
    """
    Returns full details for a transaction including related fees, refunds, and settlement items.
    Enforces merchant tenant isolation.
    """
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == transaction_id,
            Payment.merchant_id == current_user.merchant_id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found.",
        )

    fees = db.query(Fee).filter(Fee.payment_id == payment.id).all()
    refunds = db.query(Refund).filter(Refund.payment_id == payment.id).all()
    items = db.query(SettlementItem).filter(SettlementItem.payment_id == payment.id).all()

    return ApiResponse.ok(
        TransactionDetailResponse(
            payment=TransactionSummaryResponse.model_validate(payment),
            fees=[FeeSummary.model_validate(f) for f in fees],
            refunds=[RefundSummary.model_validate(r) for r in refunds],
            settlement_items=[SettlementItemSummary.model_validate(it) for it in items],
        )
    )
