import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ProposalStatus,
    ResolutionCategory,
    ResolutionEventType,
    ResolutionStatus,
)


class CreateProposalRequest(BaseModel):
    """Payload to create a new resolution proposal."""

    category: ResolutionCategory
    explanation: str = Field(
        min_length=5, description="Clear business explanation for the proposal"
    )
    proposed_action: str = Field(min_length=5, description="Recommended operational next step")
    supporting_evidence_ids: list[str] = Field(
        default_factory=list, description="List of verified evidence IDs supporting this proposal"
    )
    investigation_report_id: uuid.UUID | None = Field(
        default=None, description="Optional linked AI investigation report ID"
    )
    auto_submit: bool = Field(
        default=False, description="Whether to submit for approval immediately upon creation"
    )


class DecisionRequest(BaseModel):
    """Payload when a reviewer approves or rejects a proposal."""

    rationale: str = Field(
        min_length=3,
        description="Reviewer rationale or mandatory explanation for rejection",
    )


class ResolveExceptionRequest(BaseModel):
    """Payload to explicitly finalize exception resolution."""

    confirmation: bool = Field(
        description="Explicit confirmation acknowledging evidence and approval checks"
    )
    notes: str | None = Field(default=None, description="Optional closing operational notes")


class ReopenExceptionRequest(BaseModel):
    """Payload to reopen a previously resolved exception."""

    reason: str = Field(
        min_length=5, description="Mandatory business reason for reopening the exception"
    )


class ProposalResponse(BaseModel):
    """Detailed resolution proposal information."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    exception_id: uuid.UUID
    investigation_report_id: uuid.UUID | None
    category: ResolutionCategory
    status: ProposalStatus
    explanation: str
    proposed_action: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    created_by_user_id: uuid.UUID
    created_by_user_name: str | None = None
    created_by_user_email: str | None = None
    decision_by_user_id: uuid.UUID | None = None
    decision_by_user_name: str | None = None
    decision_rationale: str | None = None
    decided_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ResolutionHistoryItem(BaseModel):
    """Immutable audit trail event for exception resolution."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    exception_id: uuid.UUID
    proposal_id: uuid.UUID | None
    user_id: uuid.UUID
    user_name: str | None = None
    user_role: str | None = None
    event_type: ResolutionEventType
    previous_status: str
    new_status: str
    reason: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class ResolutionSummaryResponse(BaseModel):
    """Summary of current exception resolution status and operator permissions."""

    model_config = ConfigDict(from_attributes=True)

    exception_id: uuid.UUID
    resolution_status: ResolutionStatus
    active_proposal: ProposalResponse | None = None
    proposals_count: int = 0
    history_events_count: int = 0
    can_submit_proposal: bool = True
    can_approve: bool = False
    can_reject: bool = False
    can_resolve: bool = False
    can_reopen: bool = False
    allowed_transitions: list[ResolutionStatus] = Field(default_factory=list)
