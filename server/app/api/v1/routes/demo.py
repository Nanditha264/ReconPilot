from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.modules.demo.schemas import DemoScenariosResponse
from app.modules.demo.service import DemoService
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/demo", tags=["Judge & Presenter Demo Experience"])


@router.get("/scenarios", response_model=ApiResponse[DemoScenariosResponse])
def get_demo_scenarios(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[DemoScenariosResponse]:
    """
    Returns dynamically discovered real demo scenarios from accessible records
    for the authenticated merchant. Does not fabricate data or hardcode IDs.
    """
    service = DemoService(db=db, merchant_id=current_user.merchant_id)
    scenarios = service.get_scenarios()
    return ApiResponse.ok(scenarios)
