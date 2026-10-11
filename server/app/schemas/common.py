from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Any | None = Field(default=None, description="Optional diagnostic details")


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool
    data: DataT | None = None
    error: ErrorDetail | None = None

    @classmethod
    def ok(cls, data: DataT) -> "ApiResponse[DataT]":
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> "ApiResponse[None]":
        return cls(
            success=False,
            data=None,
            error=ErrorDetail(code=code, message=message, details=details),
        )
