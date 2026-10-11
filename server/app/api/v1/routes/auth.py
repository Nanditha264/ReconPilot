from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.enums import UserStatus
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponseData,
    LoginRequest,
    LoginResponseData,
    MerchantSummary,
    UserResponse,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Access"])


@router.post("/login", response_model=ApiResponse[LoginResponseData])
def login(
    credentials: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[LoginResponseData]:
    """
    Authenticate user with email and password, returning signed JWT bearer token,
    sanitized user profile, and tenant metadata.
    """
    normalized_email = credentials.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact your administrator.",
        )

    # Update last login timestamp in a managed transaction
    user.last_login_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)

    merchant = db.query(Merchant).filter(Merchant.id == user.merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User merchant organisation could not be resolved.",
        )

    token = create_access_token(
        data={
            "sub": str(user.id),
            "merchant_id": str(user.merchant_id),
            "role": user.role.value,
            "email": user.email,
        }
    )

    return ApiResponse.ok(
        LoginResponseData(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            merchant=MerchantSummary.model_validate(merchant),
        )
    )


@router.get("/me", response_model=ApiResponse[CurrentUserResponseData])
def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[CurrentUserResponseData]:
    """
    Return currently authenticated user profile and associated merchant details.
    """
    merchant = db.query(Merchant).filter(Merchant.id == current_user.merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Merchant organization not found.",
        )

    return ApiResponse.ok(
        CurrentUserResponseData(
            user=UserResponse.model_validate(current_user),
            merchant=MerchantSummary.model_validate(merchant),
        )
    )


@router.post("/logout", response_model=ApiResponse[dict[str, str]])
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict[str, str]]:
    """
    Stateless bearer logout endpoint.
    Instructs client to purge credentials from local memory/session.
    """
    return ApiResponse.ok({"message": "Successfully logged out."})
