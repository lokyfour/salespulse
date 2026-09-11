"""
pipeline/chain.py

Composes the six pipeline tasks into a Celery chain and dispatches it.

The chain is linear: each task receives the call_id and proceeds only
if the previous stage succeeded. On partial failure, the state machine
marks which stage failed so a retry re-runs only the failed stage forward.

Interface:
    dispatch_pipeline(call_id) -> AsyncResult
    resume_pipeline(call_id, from_stage) -> AsyncResult
"""

from __future__ import annotations

from uuid import UUID

from celery.result import AsyncResult

from .state import PipelineStage


def dispatch_pipeline(call_id: UUID) -> AsyncResult:
    """
    Build and dispatch the full six-stage pipeline for `call_id`.

    Returns immediately with an AsyncResult. Callers poll
    GET /calls/{call_id}/status for completion.

    Args:
        call_id: UUID of the call to process.

    Returns:
        Celery AsyncResult (task chain root).
    """
    raise NotImplementedError


def resume_pipeline(call_id: UUID, from_stage: PipelineStage) -> AsyncResult:
    """
    Resume a failed pipeline from a specific stage.

    Stages before `from_stage` are not re-run (their outputs are already
    in the database). Useful for retrying after a transient LLM API failure
    without re-running expensive ASR.

    Args:
        call_id: UUID of the call.
        from_stage: The stage at which to resume.

    Returns:
        Celery AsyncResult.
    """
    raise NotImplementedError
