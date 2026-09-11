"""
api/routes/calls.py

Call ingestion, status polling, scorecard retrieval, and GDPR erasure.

Routes:
    POST   /calls/upload              Multipart file upload
    POST   /calls/webhook/crm         CRM recording webhook
    POST   /calls/webhook/twilio      Twilio RecordingStatusCallback
    GET    /calls/{call_id}/status    Pipeline status
    GET    /calls/{call_id}/scorecard Full scorecard
    GET    /calls/{call_id}/transcript Normalised transcript
    DELETE /calls/{call_id}           GDPR Art. 17 erasure
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, UploadFile, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import (
    CallEnqueueResponse,
    CallStatusResponse,
    ScorecardResponse,
    CRMWebhookRequest,
)

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/upload", response_model=CallEnqueueResponse)
async def upload_call(
    file: UploadFile,
    rep_id: str = Form(...),
    crm_deal_id: str | None = Form(None),
    session: AsyncSession = Depends(lambda: None),   # replaced by DI in app.py
) -> CallEnqueueResponse:
    """
    Accept a call recording file, validate, deduplicate, and enqueue.

    Returns call_id immediately; processing is async.
    Poll GET /calls/{call_id}/status for completion.
    """
    raise NotImplementedError


@router.post("/webhook/crm", response_model=CallEnqueueResponse)
async def crm_webhook(
    payload: CRMWebhookRequest,
    session: AsyncSession = Depends(lambda: None),
) -> CallEnqueueResponse:
    """Receive a recording webhook from a connected CRM."""
    raise NotImplementedError


@router.post("/webhook/twilio", response_model=CallEnqueueResponse)
async def twilio_webhook(
    session: AsyncSession = Depends(lambda: None),
) -> CallEnqueueResponse:
    """
    Receive Twilio RecordingStatusCallback.
    Validates Twilio request signature before processing.
    """
    raise NotImplementedError


@router.get("/{call_id}/status", response_model=CallStatusResponse)
async def get_call_status(
    call_id: UUID,
    session: AsyncSession = Depends(lambda: None),
) -> CallStatusResponse:
    """Poll pipeline stage for a call. Returns scorecard_url when complete."""
    raise NotImplementedError


@router.get("/{call_id}/scorecard", response_model=ScorecardResponse)
async def get_scorecard(
    call_id: UUID,
    session: AsyncSession = Depends(lambda: None),
) -> ScorecardResponse:
    """Return the full scorecard for a completed call."""
    raise NotImplementedError


@router.delete("/{call_id}", status_code=204)
async def erase_call(
    call_id: UUID,
    session: AsyncSession = Depends(lambda: None),
) -> None:
    """
    GDPR Art. 17 right to erasure.

    Deletes: audio file from storage, transcript, scorecard, coaching entries.
    Irreversible. Returns 204 on success.
    """
    raise NotImplementedError
