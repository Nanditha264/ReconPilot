from collections.abc import Sequence
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import Select, asc, desc, func
from sqlalchemy.orm import Session

DataT = TypeVar("DataT")


class PaginationParams(BaseModel):
    """Reusable query parameters for pagination and sorting."""

    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")
    sort_by: str | None = Field(default=None, description="Field to sort by")
    sort_dir: Literal["asc", "desc"] = Field(default="desc", description="Sort direction")
    search: str | None = Field(default=None, description="Optional search term")


class PaginatedMeta(BaseModel):
    """Metadata describing a paginated collection."""

    total_items: int = Field(..., description="Total records across all pages")
    total_pages: int = Field(..., description="Total pages available")
    current_page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of records per page")
    has_next: bool = Field(..., description="Whether a next page exists")
    has_previous: bool = Field(..., description="Whether a previous page exists")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Standard paginated collection response envelope."""

    items: list[DataT]
    meta: PaginatedMeta


def paginate_query(
    db: Session,
    query: Select[Any],
    params: PaginationParams,
    allowed_sort_fields: dict[str, Any] | None = None,
    default_sort_column: Any | None = None,
) -> tuple[Sequence[Any], PaginatedMeta]:
    """
    Applies safe sorting, counting, and slicing to a SQLAlchemy select statement.
    Prevents SQL injection by only allowing explicitly whitelisted sort columns.
    """
    # 1. Total count query
    count_query = query.with_only_columns(func.count()).order_by(None)
    total_items = db.scalar(count_query) or 0

    # 2. Sorting application
    applied_query = query
    if params.sort_by and allowed_sort_fields and params.sort_by in allowed_sort_fields:
        col = allowed_sort_fields[params.sort_by]
        order_func = desc if params.sort_dir == "desc" else asc
        applied_query = applied_query.order_by(order_func(col))
    elif default_sort_column is not None:
        order_func = desc if params.sort_dir == "desc" else asc
        applied_query = applied_query.order_by(order_func(default_sort_column))

    # 3. Offsets and limits
    offset = (params.page - 1) * params.page_size
    applied_query = applied_query.offset(offset).limit(params.page_size)

    items = db.scalars(applied_query).all()

    total_pages = (total_items + params.page_size - 1) // params.page_size if total_items > 0 else 1
    meta = PaginatedMeta(
        total_items=total_items,
        total_pages=total_pages,
        current_page=params.page,
        page_size=params.page_size,
        has_next=params.page < total_pages,
        has_previous=params.page > 1,
    )

    return items, meta
