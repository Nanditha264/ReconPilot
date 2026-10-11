from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.session import check_db_connection
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get("", response_model=ApiResponse[dict[str, Any]])
async def health_liveness() -> ApiResponse[dict[str, Any]]:
    """
    Liveness probe: verifies that the FastAPI process is active, responding to HTTP traffic,
    and reports deployment mode and integrations configuration.
    """
    settings = get_settings()
    return ApiResponse.ok(
        {
            "status": "healthy",
            "service": "reconpilot-backend",
            "version": "0.1.0",
            "environment": settings.APP_ENV,
            "integrations": {
                "razorpay_configured": settings.has_razorpay_credentials,
                "ai_provider": settings.AI_PROVIDER,
                "llm_configured": settings.has_llm_credentials,
            },
        }
    )


@router.get("/ready", response_model=ApiResponse[dict[str, Any]])
async def health_readiness() -> JSONResponse:
    """
    Readiness probe: checks actual infrastructure dependencies.
    Verifies live PostgreSQL connection. If PostgreSQL is offline or unreachable,
    returns HTTP 503 with safe diagnostic details. Never pretends database is ready.
    """
    settings = get_settings()
    db_ok, db_message = check_db_connection()

    payload = {
        "status": "ready" if db_ok else "not_ready",
        "service": "reconpilot-backend",
        "database": {
            "type": "PostgreSQL",
            "connected": db_ok,
            "message": db_message,
        },
        "config": {
            "environment": settings.APP_ENV,
            "amount_tolerance": settings.AMOUNT_TOLERANCE,
            "ai_auto_classify_threshold": settings.AI_AUTO_CLASSIFY_THRESHOLD,
            "ai_review_threshold": settings.AI_REVIEW_THRESHOLD,
        },
    }

    if db_ok:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ApiResponse.ok(payload).model_dump(),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ApiResponse.fail(
                code="DATABASE_UNAVAILABLE",
                message="PostgreSQL database dependency is not reachable.",
                details=payload,
            ).model_dump(),
        )
