import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole, UserStatus


class TokenPayload(BaseModel):
    """Decoded JWT claims payload."""

    sub: str = Field(..., description="User UUID")
    merchant_id: str = Field(..., description="Merchant UUID")
    role: UserRole = Field(..., description="User RBAC role")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")


class LoginRequest(BaseModel):
    """User credentials for authentication."""

    email: str = Field(
        ..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Registered user email address"
    )
    password: str = Field(..., min_length=8, description="User password")


class UserResponse(BaseModel):
    """Sanitized user profile without sensitive fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    last_login_at: datetime | None = None
    created_at: datetime


class MerchantSummary(BaseModel):
    """Tenant summary associated with an authenticated user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    currency: str
    timezone: str


class LoginResponseData(BaseModel):
    """Data payload for successful login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    merchant: MerchantSummary


class CurrentUserResponseData(BaseModel):
    """Data payload for current authenticated user profile."""

    user: UserResponse
    merchant: MerchantSummary
