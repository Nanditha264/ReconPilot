from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.common import ApiResponse
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    paginate_query,
)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=ApiResponse[PaginatedResponse[UserResponse]])
def list_users(
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str | None = Query(default="created_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    search: str | None = Query(default=None),
) -> ApiResponse[PaginatedResponse[UserResponse]]:
    """
    List merchant users with pagination, sorting and search.
    Requires ADMIN role and enforces merchant tenant isolation.
    """
    params = PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,  # type: ignore[arg-type]
        search=search,
    )

    query = select(User).where(User.merchant_id == current_user.merchant_id)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(User.email.ilike(search_filter) | User.full_name.ilike(search_filter))

    allowed_sort_fields = {
        "email": User.email,
        "full_name": User.full_name,
        "role": User.role,
        "status": User.status,
        "created_at": User.created_at,
        "last_login_at": User.last_login_at,
    }

    items, meta = paginate_query(
        db=db,
        query=query,
        params=params,
        allowed_sort_fields=allowed_sort_fields,
        default_sort_column=User.created_at,
    )

    return ApiResponse.ok(
        PaginatedResponse(
            items=[UserResponse.model_validate(u) for u in items],
            meta=meta,
        )
    )
