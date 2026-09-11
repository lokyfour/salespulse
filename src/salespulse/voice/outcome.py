"""
voice/outcome.py

Parses the voice agent session result into a format suitable for
ingestion into the main scoring pipeline.

After a call ends, the session transcript + outcome are packaged into
a CallIngestionPayload and submitted to the pipeline ingest layer
(same path as a recorded call upload — voice agent calls get scored
with the same rubric as recorded calls).

Interface:
    SessionResult          — output of VoiceAgentSession.finalise()
    build_ingestion_payload(result) -> CallIngestionPayload
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .agent import CallOutcomeSignal


@dataclass
class SessionResult:
    """Complete result of a finished voice agent call session."""

    call_sid: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float
    turns: list[dict]              # [{speaker, text, timestamp}]
    outcome: CallOutcomeSignal
    appointment_id: str | None     # Set when outcome=APPOINTMENT_BOOKED
    lead_data: dict                # Original lead data passed to session
    raw_transcript: str            # Full text, line-per-turn


@dataclass
class CallIngestionPayload:
    """Payload submitted to the main pipeline after a voice agent call."""

    source: str = "voice_agent"
    call_sid: str = ""
    rep_id: str = ""
    crm_deal_id: str | None = None
    transcript_text: str = ""     # Pre-transcribed — skips ASR stage
    duration_seconds: float = 0.0
    outcome: str = ""
    metadata: dict = field(default_factory=dict)


def build_ingestion_payload(
    result: SessionResult,
    rep_id: str,
    crm_deal_id: str | None = None,
) -> CallIngestionPayload:
    """
    Convert a SessionResult into a CallIngestionPayload for the pipeline.

    Voice agent calls skip the ASR stage (transcript is already available)
    and enter the pipeline at the diarization stage with speaker labels
    pre-assigned (agent = rep, prospect = prospect).

    Args:
        result: Completed session result from VoiceAgentSession.finalise().
        rep_id: Internal rep ID for the agent.
        crm_deal_id: Optional CRM deal to update with the call result.

    Returns:
        CallIngestionPayload ready for pipeline submission.
    """
    raise NotImplementedError
