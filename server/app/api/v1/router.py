from fastapi import APIRouter

from app.api.v1.routes import (
    audit,
    auth,
    dashboard,
    demo,
    exceptions,
    health,
    ingestion,
    reconciliation,
    transactions,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(ingestion.router)
api_router.include_router(reconciliation.router)
api_router.include_router(transactions.router)
api_router.include_router(exceptions.router)
api_router.include_router(dashboard.router)
api_router.include_router(demo.router)
api_router.include_router(audit.router)
