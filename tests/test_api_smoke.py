"""
tests/test_api_smoke.py

FastAPI smoke tests using TestClient. enqueue_call and get_call_result are
mocked so these tests exercise the HTTP layer only (routing, validation,
status codes, background cleanup wiring) — not the pipeline itself.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from salespulse.api.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_returns_call_id(client, monkeypatch):
    monkeypatch.setattr(
        "salespulse.pipeline.tasks.enqueue_call",
        lambda audio_path, rep_id, crm_deal_id=None: "fixed-call-id",
    )
    response = client.post(
        "/calls/upload",
        files={"file": ("call.mp3", io.BytesIO(b"fake audio bytes"), "audio/mpeg")},
        data={"rep_id": "rep_123"},
    )
    assert response.status_code == 200
    assert response.json() == {"call_id": "fixed-call-id", "status": "queued"}


def test_upload_missing_rep_id_returns_422(client):
    response = client.post(
        "/calls/upload",
        files={"file": ("call.mp3", io.BytesIO(b"fake audio bytes"), "audio/mpeg")},
    )
    assert response.status_code == 422


def test_upload_missing_file_returns_422(client):
    response = client.post("/calls/upload", data={"rep_id": "rep_123"})
    assert response.status_code == 422


def test_status_returns_queued(client, monkeypatch):
    monkeypatch.setattr(
        "salespulse.pipeline.tasks.get_call_result",
        lambda call_id: {"call_id": call_id, "stage": "queued"},
    )
    response = client.get("/calls/some-call-id/status")
    assert response.status_code == 200
    assert response.json()["stage"] == "queued"


def test_status_returns_complete_with_scorecard(client, monkeypatch):
    staged_response = {
        "call_id": "some-call-id",
        "stage": "complete",
        "overall_score": 71,
        "coaching_flags": ["Champion not identified"],
        "criteria_scores": [
            {
                "criterion_id": "metrics",
                "label": "Metrics",
                "score": 2,
                "weight": 20,
                "evidence": "quote",
                "timestamp": "00:15",
                "flag": None,
            }
        ],
        "conversation_metrics": {
            "talk_ratio": 0.48,
            "next_step_confirmed": True,
            "objections_handled": 0,
            "competitor_mentions": [],
        },
        "overall_notes": "Good call.",
    }
    monkeypatch.setattr(
        "salespulse.pipeline.tasks.get_call_result",
        lambda call_id: staged_response,
    )
    response = client.get("/calls/some-call-id/status")
    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "complete"
    assert body["overall_score"] == 71
    assert len(body["criteria_scores"]) == 1


def test_status_unknown_call_returns_404(client, monkeypatch):
    monkeypatch.setattr(
        "salespulse.pipeline.tasks.get_call_result",
        lambda call_id: {"error": "call_not_found"},
    )
    response = client.get("/calls/does-not-exist/status")
    assert response.status_code == 404


def test_upload_tempfile_cleaned_up(client, monkeypatch):
    calls = []

    def fake_add_task(self, func, *args, **kwargs):
        calls.append((func, args, kwargs))

    monkeypatch.setattr(
        "fastapi.BackgroundTasks.add_task",
        fake_add_task,
    )
    monkeypatch.setattr(
        "salespulse.pipeline.tasks.enqueue_call",
        lambda audio_path, rep_id, crm_deal_id=None: "fixed-call-id",
    )
    response = client.post(
        "/calls/upload",
        files={"file": ("call.mp3", io.BytesIO(b"fake audio bytes"), "audio/mpeg")},
        data={"rep_id": "rep_123"},
    )
    assert response.status_code == 200
    assert len(calls) == 1
    func, args, kwargs = calls[0]
    import os

    assert func is os.unlink
    assert len(args) == 1 and isinstance(args[0], str)
