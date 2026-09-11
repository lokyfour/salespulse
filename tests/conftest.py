"""
tests/conftest.py

Shared fixtures for the salespulse test suite.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
RUBRIC_PATH = Path(__file__).parent.parent / "config" / "rubric.example.yaml"


@pytest.fixture
def rubric():
    """Load the real example rubric (6 MEDDIC criteria, weights sum to 100)."""
    from salespulse.scoring.rubric import load_rubric

    return load_rubric(RUBRIC_PATH)


@pytest.fixture
def sample_transcript():
    """Canonical Transcript built from tests/fixtures/sample_transcript.json."""
    from salespulse.transcript.normaliser import normalise_from_fixture

    return normalise_from_fixture(FIXTURES_DIR / "sample_transcript.json", uuid.uuid4())


@pytest.fixture
def expected_scorecard_dict():
    """Raw dict loaded from tests/fixtures/expected_scorecard.json."""
    import json

    with open(FIXTURES_DIR / "expected_scorecard.json") as f:
        return json.load(f)


@pytest.fixture
def mock_llm_response():
    """
    A valid scorecard dict matching the LLM response schema in
    prompt_builder.py, scoring all 6 MEDDIC criteria from
    config/rubric.example.yaml. Evidence quotes are verbatim substrings of
    tests/fixtures/sample_transcript.json turns so evidence verification
    succeeds.
    """
    return {
        "criteria_scores": [
            {
                "criterion_id": "metrics",
                "score": 2,
                "evidence": (
                    "Yes exactly. We've had a rough quarter — close rate "
                    "dropped from 28 to 19 percent over six months and I'm "
                    "getting pressure from the VP to turn that around before "
                    "end of year."
                ),
                "timestamp": "00:15",
                "flag": None,
            },
            {
                "criterion_id": "economic_buyer",
                "score": 3,
                "evidence": (
                    "It'd be a joint decision. I can evaluate and recommend, "
                    "but Sarah Chen — she's our VP of Sales — she'd need to "
                    "approve the budget. She's very data-driven, so I'd need "
                    "solid numbers to bring to her."
                ),
                "timestamp": "01:32",
                "flag": None,
            },
            {
                "criterion_id": "decision_criteria",
                "score": 2,
                "evidence": (
                    "Usually a pilot first — she likes to see results on "
                    "real calls before committing. We'd also need a "
                    "security review from IT, that typically takes two to "
                    "three weeks."
                ),
                "timestamp": "02:15",
                "flag": None,
            },
            {
                "criterion_id": "decision_process",
                "score": 2,
                "evidence": None,
                "timestamp": None,
                "flag": None,
            },
            {
                "criterion_id": "identify_pain",
                "score": 3,
                "evidence": (
                    "Mostly at the discovery stage. Reps are moving deals "
                    "forward without really qualifying them. We don't have "
                    "visibility into what's being said on calls, so we "
                    "can't coach at scale."
                ),
                "timestamp": "00:53",
                "flag": None,
            },
            {
                "criterion_id": "champion",
                "score": 1,
                "evidence": None,
                "timestamp": None,
                "flag": "low_score",
            },
        ],
        "conversation_metrics": {
            "talk_ratio": 0.48,
            "next_step_confirmed": True,
            "objections_handled": 0,
            "competitor_mentions": [],
        },
        "overall_notes": (
            "Strong discovery call. Economic buyer named, pain confirmed "
            "with consequence, clear next step."
        ),
    }


@pytest.fixture
def fake_redis():
    """A fresh, isolated fakeredis.FakeRedis instance."""
    import fakeredis

    return fakeredis.FakeRedis(decode_responses=True)
