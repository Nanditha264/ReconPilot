import uuid
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class DemoScenarioKey(StrEnum):
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    MISSING_PAYMENT = "MISSING_PAYMENT"
    MISSING_SETTLEMENT = "MISSING_SETTLEMENT"
    REFUND_MISMATCH = "REFUND_MISMATCH"
    FEE_MISMATCH = "FEE_MISMATCH"
    DELAYED_SETTLEMENT = "DELAYED_SETTLEMENT"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class DemoScenarioItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scenario_key: str
    title: str
    description: str
    exception_type: str
    available: bool
    exception_id: uuid.UUID | None = None
    financial_impact: str | None = None
    currency: str | None = None
    reference_id: str | None = None
    tags: list[str] = []


class DemoScenariosResponse(BaseModel):
    merchant_id: uuid.UUID
    is_demo_mode: bool
    scenarios: list[DemoScenarioItem]
    total_available: int
