import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    paginate_query,
)

router = APIRouter(prefix="/audit", tags=["Audit Trail & Governance"])


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    exception_id: uuid.UUID | None
    reconciliation_run_id: uuid.UUID | None
    actor_type: str
    actor_id: str | None
    event_type: str
    previous_state: str | None
    new_state: str | None
    event_metadata: dict[str, Any] | None
    created_at: datetime


@router.get("/events", response_model=ApiResponse[PaginatedResponse[AuditEventResponse]])
def list_audit_events(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str | None = Query(default="created_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    event_type: str | None = Query(default=None),
    actor_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> ApiResponse[PaginatedResponse[AuditEventResponse]]:
    """
    Returns paginated audit events strictly scoped to the authenticated merchant.
    Maintains complete audit provenance and tenant isolation.
    """
    params = PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,  # type: ignore[arg-type]
    )

    query = select(AuditEvent).where(AuditEvent.merchant_id == current_user.merchant_id)

    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    if actor_type:
        query = query.where(AuditEvent.actor_type == actor_type)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(
            AuditEvent.event_type.ilike(search_filter)
            | AuditEvent.actor_id.ilike(search_filter)
            | AuditEvent.new_state.ilike(search_filter)
        )

    allowed_sort_fields = {
        "created_at": AuditEvent.created_at,
        "event_type": AuditEvent.event_type,
        "actor_type": AuditEvent.actor_type,
    }

    items, meta = paginate_query(
        db=db,
        query=query,
        params=params,
        allowed_sort_fields=allowed_sort_fields,
        default_sort_column=AuditEvent.created_at,
    )

    return ApiResponse.ok(
        PaginatedResponse(
            items=[AuditEventResponse.model_validate(item) for item in items],
            meta=meta,
        )
    )
