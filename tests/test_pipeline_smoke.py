"""
tests/test_pipeline_smoke.py

Full pipeline smoke test — no real LLM, no real Redis/broker, no real DB.

Only the LLM call (scoring/llm_scorer.get_scorer) is mocked; everything
else is real code, including the actual Celery task chain
(transcribe_audio -> diarize_audio -> normalise_transcript ->
score_transcript -> generate_coaching -> push_to_crm) and the real
Redis-backed state machine (backed by fakeredis instead of a live Redis).

Celery's `task_always_eager` makes every `.delay()` call inside the task
chain execute synchronously in-process instead of talking to a broker —
this is the standard way to run a full Celery task chain "directly" in
tests without a running worker or broker.
"""

from __future__ import annotations

import copy
import uuid

import fakeredis
import pytest


@pytest.fixture(autouse=True)
def isolated_pipeline_env(monkeypatch):
    """Fresh fakeredis-backed state store + eager Celery for every test."""
    from salespulse.pipeline import state as state_module
    from salespulse.pipeline import tasks as tasks_module

    server = fakeredis.FakeServer()

    class _FakeRedisClass:
        @staticmethod
        def from_url(url, **kwargs):
            return fakeredis.FakeRedis(server=server, **kwargs)

    monkeypatch.setattr(state_module.redis, "Redis", _FakeRedisClass)

    tasks_module.app.conf.task_always_eager = True
    tasks_module.app.conf.task_eager_propagates = True

    # Isolate the mock in-memory call/transcript stores per test.
    monkeypatch.setattr(tasks_module, "_call_store", {})
    monkeypatch.setattr(tasks_module, "_transcript_store", {})

    monkeypatch.delenv("CRM_ADAPTER", raising=False)

    yield


class MockScorer:
    """Stand-in for a real LLMScorer — never calls out to a network."""

    def __init__(self, response: dict):
        self._response = response

    def score(self, system_prompt: str, user_prompt: str) -> dict:
        return copy.deepcopy(self._response)


def _run_pipeline(monkeypatch, llm_response: dict) -> str:
    from salespulse.pipeline import tasks

    monkeypatch.setattr(
        "salespulse.scoring.llm_scorer.get_scorer",
        lambda config: MockScorer(llm_response),
    )

    call_id = tasks.enqueue_call(
        audio_path="/tmp/does-not-matter.mp3",
        rep_id="rep_123",
    )
    return call_id


def test_smoke_pipeline_reaches_complete(monkeypatch, mock_llm_response):
    from salespulse.pipeline import tasks
    from salespulse.pipeline.state import PipelineStage

    call_id = _run_pipeline(monkeypatch, mock_llm_response)
    result = tasks.get_call_result(call_id)
    assert result["stage"] == PipelineStage.COMPLETE.value


def test_smoke_pipeline_overall_score_in_range(monkeypatch, mock_llm_response):
    from salespulse.pipeline import tasks

    call_id = _run_pipeline(monkeypatch, mock_llm_response)
    result = tasks.get_call_result(call_id)
    assert 0 <= result["overall_score"] <= 100


def test_smoke_pipeline_has_criteria_scores(monkeypatch, mock_llm_response):
    from salespulse.pipeline import tasks

    call_id = _run_pipeline(monkeypatch, mock_llm_response)
    result = tasks.get_call_result(call_id)
    assert len(result["criteria_scores"]) == 6
    for cs in result["criteria_scores"]:
        assert 0 <= cs["score"] <= 3


def test_smoke_pipeline_coaching_flags_are_strings(monkeypatch, mock_llm_response):
    from salespulse.pipeline import tasks

    call_id = _run_pipeline(monkeypatch, mock_llm_response)
    result = tasks.get_call_result(call_id)
    assert isinstance(result["coaching_flags"], list)
    assert all(isinstance(flag, str) for flag in result["coaching_flags"])


def test_smoke_pipeline_status_response_structure(monkeypatch, mock_llm_response):
    from salespulse.pipeline import tasks

    call_id = _run_pipeline(monkeypatch, mock_llm_response)
    result = tasks.get_call_result(call_id)
    for key in (
        "call_id",
        "stage",
        "overall_score",
        "coaching_flags",
        "criteria_scores",
        "conversation_metrics",
        "overall_notes",
    ):
        assert key in result


def test_smoke_pipeline_null_score_in_llm_response_does_not_crash(monkeypatch, mock_llm_response):
    from salespulse.pipeline import tasks
    from salespulse.pipeline.state import PipelineStage

    broken_response = copy.deepcopy(mock_llm_response)
    broken_response["criteria_scores"][0]["score"] = None

    call_id = _run_pipeline(monkeypatch, broken_response)
    result = tasks.get_call_result(call_id)
    assert result["stage"] == PipelineStage.COMPLETE.value


def test_smoke_pipeline_missing_criterion_in_llm_response_filled(monkeypatch, mock_llm_response):
    from salespulse.pipeline import tasks

    incomplete_response = copy.deepcopy(mock_llm_response)
    incomplete_response["criteria_scores"] = incomplete_response["criteria_scores"][:-1]

    call_id = _run_pipeline(monkeypatch, incomplete_response)
    result = tasks.get_call_result(call_id)
    assert len(result["criteria_scores"]) == 6
    filled = [cs for cs in result["criteria_scores"] if cs["flag"] == "not_scored_by_llm"]
    assert len(filled) == 1


def test_smoke_pipeline_crm_adapter_not_implemented_still_completes(monkeypatch, mock_llm_response):
    """
    bug #8: CRMRegistry.get() raises NotImplementedError (it's a stub).
    push_to_crm must catch that and still reach COMPLETE instead of
    crashing the pipeline.
    """
    from salespulse.pipeline import tasks
    from salespulse.pipeline.state import PipelineStage

    monkeypatch.setenv("CRM_ADAPTER", "hubspot")
    call_id = _run_pipeline(monkeypatch, mock_llm_response)
    result = tasks.get_call_result(call_id)
    assert result["stage"] == PipelineStage.COMPLETE.value


def test_get_call_result_unknown_call_returns_error():
    from salespulse.pipeline import tasks

    result = tasks.get_call_result(str(uuid.uuid4()))
    assert result == {"error": "call_not_found"}
