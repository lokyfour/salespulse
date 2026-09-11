"""
tests/test_state.py

Unit tests for pipeline/state.py (Redis-backed state machine).
Uses fakeredis so no real Redis instance is required.
"""

from __future__ import annotations

import uuid

import pytest

import fakeredis

from salespulse.pipeline import state


@pytest.fixture(autouse=True)
def isolated_fake_redis(monkeypatch):
    """
    Patch salespulse.pipeline.state.redis.Redis with a fakeredis-backed
    class, bound to a fresh FakeServer per test so tests never share state
    (each test gets a clean in-memory Redis) even though state.py itself
    creates a new client per call (no module-level caching, on purpose —
    that's what makes state visible across separate processes/workers).
    """
    server = fakeredis.FakeServer()

    class _FakeRedisClass:
        @staticmethod
        def from_url(url, **kwargs):
            return fakeredis.FakeRedis(server=server, **kwargs)

    monkeypatch.setattr(state.redis, "Redis", _FakeRedisClass)
    yield


def test_register_sets_queued():
    call_id = uuid.uuid4()
    state.register(call_id)
    assert state.get_stage(call_id) == state.PipelineStage.QUEUED


def test_advance_happy_path():
    call_id = uuid.uuid4()
    state.register(call_id)
    state.advance(call_id, state.PipelineStage.TRANSCRIBING)
    assert state.get_stage(call_id) == state.PipelineStage.TRANSCRIBING


def test_advance_all_valid_transitions_in_sequence():
    call_id = uuid.uuid4()
    state.register(call_id)
    ordered_stages = [
        state.PipelineStage.TRANSCRIBING,
        state.PipelineStage.DIARIZING,
        state.PipelineStage.NORMALISING,
        state.PipelineStage.SCORING,
        state.PipelineStage.COACHING,
        state.PipelineStage.SYNCING_CRM,
        state.PipelineStage.COMPLETE,
    ]
    for stage in ordered_stages:
        state.advance(call_id, stage)
        assert state.get_stage(call_id) == stage


def test_advance_invalid_transition_raises():
    call_id = uuid.uuid4()
    state.register(call_id)
    with pytest.raises(ValueError):
        state.advance(call_id, state.PipelineStage.SCORING)


def test_fail_sets_failed_stage():
    call_id = uuid.uuid4()
    state.register(call_id)
    state.advance(call_id, state.PipelineStage.TRANSCRIBING)
    state.fail(call_id, state.PipelineStage.TRANSCRIBING, "boom")
    assert state.get_stage(call_id) == state.PipelineStage.FAILED


def test_retry_does_not_permanently_fail():
    """
    bug #2: a Celery retry re-enters the task and calls advance() again for
    the stage the task was already in. advance() must be idempotent for
    same-stage re-entry instead of raising, so a retried task can actually
    retry the real work instead of immediately hitting an invalid-transition
    error.
    """
    call_id = uuid.uuid4()
    state.register(call_id)
    state.advance(call_id, state.PipelineStage.TRANSCRIBING)
    # Simulate task re-entry after a Celery retry: advance() is called again
    # for the same stage the task is already in.
    state.advance(call_id, state.PipelineStage.TRANSCRIBING)
    assert state.get_stage(call_id) == state.PipelineStage.TRANSCRIBING


def test_get_stage_unknown_call_raises_key_error():
    with pytest.raises(KeyError):
        state.get_stage(uuid.uuid4())


def test_get_error_returns_none_when_no_error():
    call_id = uuid.uuid4()
    state.register(call_id)
    assert state.get_error(call_id) is None


def test_get_error_returns_message_after_fail():
    call_id = uuid.uuid4()
    state.register(call_id)
    state.advance(call_id, state.PipelineStage.TRANSCRIBING)
    state.fail(call_id, state.PipelineStage.TRANSCRIBING, "network timeout")
    error = state.get_error(call_id)
    assert error is not None
    assert "network timeout" in error


def test_state_visible_across_two_client_instances():
    """
    bug #1: state must be visible to a second, independently-constructed
    client (simulating the API process reading state written by a Celery
    worker process).
    """
    call_id = uuid.uuid4()
    state.register(call_id)
    state.advance(call_id, state.PipelineStage.TRANSCRIBING)

    # A fresh client, as a different process/module import would create.
    other_client = state._get_client()
    raw = other_client.get(state._state_key(call_id))
    assert raw == state.PipelineStage.TRANSCRIBING.value
