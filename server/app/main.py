from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.middleware.error_handler import register_exception_handlers


def create_app() -> FastAPI:
    """Application factory for ReconPilot FastAPI backend."""
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title="ReconPilot API",
        description="AI Finance Controller backend for evidence-backed financial reconciliation.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register standardized exception handlers
    register_exception_handlers(app)

    # Register API v1 routes
    app.include_router(api_router)

    return app


app = create_app()
