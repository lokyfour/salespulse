"""
tests/test_evidence.py

Unit tests for scoring/evidence.py — quote verification and timestamp
resolution.
"""

from __future__ import annotations

import uuid

from salespulse.scoring.evidence import resolve_timestamp, verify_evidence
from salespulse.transcript.models import Transcript, Turn


def _transcript(duration_seconds=200.0):
    turns = [
        Turn(
            speaker="prospect",
            start=15.0,
            end=34.0,
            text="close rate dropped from 28 to 19 percent over six months",
            words=[],
        ),
        Turn(
            speaker="rep",
            start=35.0,
            end=52.0,
            text="that's a meaningful drop in performance",
            words=[],
        ),
    ]
    return Transcript(
        call_id=uuid.uuid4(),
        turns=turns,
        language="en",
        duration_seconds=duration_seconds,
        asr_provider="mock",
        rep_speaker_id="rep",
    )


def test_exact_quote_verified():
    t = _transcript()
    result = verify_evidence(
        "close rate dropped from 28 to 19 percent over six months", t
    )
    assert result.verified is True
    assert result.matched_turn is not None
    assert result.resolved_seconds == 15.0


def test_close_quote_above_threshold_verified():
    t = _transcript()
    # Minor transcription variant — drops one word, still >= 0.75 overlap.
    result = verify_evidence(
        "close rate dropped from 28 to 19 percent over months", t
    )
    assert result.verified is True


def test_unrelated_quote_not_verified():
    t = _transcript()
    result = verify_evidence("this text never appeared anywhere in the call", t)
    assert result.verified is False


def test_empty_quote_not_verified():
    t = _transcript()
    result = verify_evidence("", t)
    assert result.verified is False
    assert result.match_score == 0.0
    assert result.matched_turn is None


def test_resolve_timestamp_mm_ss():
    t = _transcript()
    assert resolve_timestamp("01:30", t) == 90.0


def test_resolve_timestamp_hh_mm_ss():
    t = _transcript(duration_seconds=4000.0)
    assert resolve_timestamp("01:02:03", t) == 3723.0


def test_resolve_timestamp_invalid_string_returns_none():
    t = _transcript()
    assert resolve_timestamp("not-a-timestamp", t) is None


def test_resolve_timestamp_beyond_duration_returns_none():
    t = _transcript(duration_seconds=100.0)
    assert resolve_timestamp("05:00", t) is None
