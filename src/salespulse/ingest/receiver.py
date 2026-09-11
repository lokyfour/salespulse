"""
ingest/receiver.py

Accepts call recordings from three entry points and enqueues them
for pipeline processing:

  1. Direct file upload (multipart/form-data)
  2. CRM webhook (Salesforce, HubSpot) — recording URL + deal metadata
  3. Twilio recording webhook — recording URL fired after call ends

Interface:
    handle_upload(file, rep_id, crm_deal_id, session) -> CallEnqueueResult
    handle_crm_webhook(payload: CRMWebhookPayload, session) -> CallEnqueueResult
    handle_twilio_webhook(payload: TwilioRecordingPayload, session) -> CallEnqueueResult
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class CallEnqueueResult:
    """Returned to the API layer after a call is accepted for processing."""

    call_id: UUID
    status: str  # "queued" | "duplicate" | "rejected"
    rejection_reason: str | None


class CRMWebhookPayload:
    """Normalised payload from any supported CRM recording webhook."""

    crm_type: str  # "hubspot" | "salesforce" | "pipedrive"
    crm_deal_id: str
    recording_url: str
    rep_email: str | None
    duration_seconds: int | None
    raw: dict  # Original webhook body for audit


class TwilioRecordingPayload:
    """Payload from Twilio's RecordingStatusCallback webhook."""

    call_sid: str
    recording_sid: str
    recording_url: str
    duration: int
    channels: int


async def handle_upload(
    file_path: Path,
    rep_id: str,
    crm_deal_id: str | None,
    session: AsyncSession,
) -> CallEnqueueResult:
    """
    Accept a directly uploaded audio file, validate it, persist a Call
    record, and enqueue the pipeline.

    Args:
        file_path: Temporary path where the uploaded file was saved.
        rep_id: Internal rep identifier.
        crm_deal_id: Optional CRM deal ID for result sync.
        session: Active async SQLAlchemy session.

    Returns:
        CallEnqueueResult with call_id and status.
    """
    raise NotImplementedError


async def handle_crm_webhook(
    payload: CRMWebhookPayload,
    session: AsyncSession,
) -> CallEnqueueResult:
    """
    Process a recording webhook from a CRM. Downloads the recording URL,
    validates the audio, deduplicates by (crm_type, crm_deal_id), and
    enqueues if new.

    Args:
        payload: Normalised CRM webhook payload.
        session: Active async SQLAlchemy session.

    Returns:
        CallEnqueueResult. status="duplicate" if already processed.
    """
    raise NotImplementedError


async def handle_twilio_webhook(
    payload: TwilioRecordingPayload,
    session: AsyncSession,
) -> CallEnqueueResult:
    """
    Process Twilio's RecordingStatusCallback. Downloads the .mp3 from
    the recording URL, validates, deduplicates by recording_sid, enqueues.

    Args:
        payload: Twilio recording webhook fields.
        session: Active async SQLAlchemy session.

    Returns:
        CallEnqueueResult.
    """
    raise NotImplementedError
