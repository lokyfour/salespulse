"""
pipeline/state.py

Call processing state machine — Redis-backed so that state is visible
across the API process and every Celery worker process.

Key schema:
    salespulse:state:{call_id}  → stage string
    salespulse:error:{call_id}  → error string
"""

from __future__ import annotations

import os
from enum import StrEnum
from uuid import UUID

import redis


class PipelineStage(StrEnum):
    QUEUED = "queued"
    TRANSCRIBING = "transcribing"
    DIARIZING = "diarizing"
    NORMALISING = "normalising"
    SCORING = "scoring"
    COACHING = "coaching"
    SYNCING_CRM = "syncing_crm"
    COMPLETE = "complete"
    FAILED = "failed"


TRANSITIONS: dict[PipelineStage, PipelineStage] = {
    PipelineStage.QUEUED: PipelineStage.TRANSCRIBING,
    PipelineStage.TRANSCRIBING: PipelineStage.DIARIZING,
    PipelineStage.DIARIZING: PipelineStage.NORMALISING,
    PipelineStage.NORMALISING: PipelineStage.SCORING,
    PipelineStage.SCORING: PipelineStage.COACHING,
    PipelineStage.COACHING: PipelineStage.SYNCING_CRM,
    PipelineStage.SYNCING_CRM: PipelineStage.COMPLETE,
}

STATE_KEY_PREFIX = "salespulse:state:"
ERROR_KEY_PREFIX = "salespulse:error:"


def _get_client() -> redis.Redis:
    """
    Build a Redis client from REDIS_URL.

    Not cached at module scope: tests (and process forks) need to be able to
    swap the backing client without fighting a stale cached connection.
    """
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(redis_url, decode_responses=True)


def _state_key(call_id: UUID) -> str:
    return f"{STATE_KEY_PREFIX}{call_id}"


def _error_key(call_id: UUID) -> str:
    return f"{ERROR_KEY_PREFIX}{call_id}"


def advance(call_id: UUID, stage: PipelineStage) -> None:
    client = _get_client()
    key = _state_key(call_id)
    raw = client.get(key)
    current = PipelineStage(raw) if raw else PipelineStage.QUEUED

    if current == stage:
        # Idempotent: a Celery retry re-enters the task and calls advance()
        # for the stage it was already in when the failure occurred.
        return

    expected_next = TRANSITIONS.get(current)
    if expected_next != stage:
        raise ValueError(f"Invalid transition {current} → {stage}. Expected next: {expected_next}")
    client.set(key, stage.value)


def fail(call_id: UUID, failed_at_stage: PipelineStage, error_message: str) -> None:
    client = _get_client()
    client.set(_state_key(call_id), PipelineStage.FAILED.value)
    client.set(_error_key(call_id), f"{failed_at_stage}: {error_message}")


def get_stage(call_id: UUID) -> PipelineStage:
    client = _get_client()
    raw = client.get(_state_key(call_id))
    if raw is None:
        raise KeyError(f"Call {call_id} not found in state store")
    return PipelineStage(raw)


def register(call_id: UUID) -> None:
    """Register a new call in the state machine at QUEUED."""
    client = _get_client()
    client.set(_state_key(call_id), PipelineStage.QUEUED.value)


def get_error(call_id: UUID) -> str | None:
    client = _get_client()
    return client.get(_error_key(call_id))
