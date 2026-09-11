"""
api/schemas.py

Pydantic request and response schemas for the FastAPI layer.

Schemas are versioned by module (v1). Breaking changes require a new
schema version, not in-place modification.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────────────
# Request schemas
# ──────────────────────────────────────────────────────────────────────


class UploadMetadata(BaseModel):
    """Form fields accompanying a file upload."""

    rep_id: str = Field(..., description="Internal rep identifier")
    crm_deal_id: str | None = Field(None, description="CRM deal ID for result sync")


class CRMWebhookRequest(BaseModel):
    """Normalised webhook payload from a CRM recording event."""

    crm_type: str
    crm_deal_id: str
    recording_url: str
    rep_email: str | None = None
    duration_seconds: int | None = None


# ──────────────────────────────────────────────────────────────────────
# Response schemas
# ──────────────────────────────────────────────────────────────────────


class CallEnqueueResponse(BaseModel):
    call_id: UUID
    status: str  # "queued" | "duplicate" | "rejected"
    rejection_reason: str | None = None


class CallStatusResponse(BaseModel):
    call_id: UUID
    stage: str  # PipelineStage value
    overall_score: int | None = None
    scorecard_url: str | None = None
    error_message: str | None = None
    updated_at: datetime


class CriterionScoreResponse(BaseModel):
    criterion_id: str
    label: str
    score: int
    weight: int
    evidence: str | None
    timestamp: str | None
    flag: str | None


class ScorecardResponse(BaseModel):
    call_id: UUID
    rubric_name: str
    overall_score: int
    criteria_scores: list[CriterionScoreResponse]
    talk_ratio: float
    next_step_confirmed: bool
    objections_handled: int
    competitor_mentions: list[str]
    coaching_flags: list[str]
    overall_notes: str


class CoachingFlagResponse(BaseModel):
    severity: str
    criterion_id: str | None
    title: str
    recommendation: str
    evidence_summary: str


class RepDashboardResponse(BaseModel):
    rep_id: str
    average_overall_score: float
    score_trend_direction: str
    calls_analysed: int
    flags: list[CoachingFlagResponse]
    top_strength: str | None
    top_weakness: str | None


class TeamReportResponse(BaseModel):
    team_id: str
    rep_count: int
    average_overall_score: float
    underperformers: list[str]
    top_performers: list[str]
    top_objections: list[str]
    competitor_leaderboard: list[dict]


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    workers: int
    queue: str  # "idle" | "busy" | "unavailable"
    db: str  # "ok" | "unavailable"
