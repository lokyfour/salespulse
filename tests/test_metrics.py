"""
tests/test_metrics.py

Unit tests for scoring/metrics.py rule-based conversation metrics.
"""

from __future__ import annotations

import uuid

from salespulse.scoring.metrics import (
    ComputedMetrics,
    MetricsConfig,
    compute_metrics,
    detect_competitors,
)
from salespulse.transcript.models import Transcript, Turn


def _turn(speaker, start, end, text):
    return Turn(speaker=speaker, start=start, end=end, text=text, words=[])


def _transcript(turns, duration_seconds, rep_speaker_id="rep"):
    return Transcript(
        call_id=uuid.uuid4(),
        turns=turns,
        language="en",
        duration_seconds=duration_seconds,
        asr_provider="mock",
        rep_speaker_id=rep_speaker_id,
    )


def test_talk_ratio_correct(sample_transcript):
    metrics = compute_metrics(sample_transcript, MetricsConfig())
    assert metrics.talk_ratio == sample_transcript.rep_talk_ratio
    assert 0.0 <= metrics.talk_ratio <= 1.0


def test_talk_ratio_zero_duration_safe():
    t = _transcript([_turn("rep", 0.0, 0.0, "hello")], duration_seconds=0.0)
    metrics = compute_metrics(t, MetricsConfig())
    assert metrics.talk_ratio == 0.0


def test_next_step_detected():
    turns = [
        _turn("rep", 0.0, 5.0, "let's get started"),
        _turn("prospect", 5.0, 10.0, "sounds good"),
        _turn(
            "rep",
            10.0,
            15.0,
            "great, I'll send over the proposal and let's schedule a call Thursday",
        ),
    ]
    t = _transcript(turns, duration_seconds=15.0)
    metrics = compute_metrics(t, MetricsConfig())
    assert metrics.next_step_confirmed is True


def test_next_step_not_detected():
    turns = [
        _turn("rep", 0.0, 5.0, "thanks for your time today"),
        _turn("prospect", 5.0, 10.0, "sure, no problem"),
    ]
    t = _transcript(turns, duration_seconds=10.0)
    metrics = compute_metrics(t, MetricsConfig())
    assert metrics.next_step_confirmed is False


def test_competitor_detected():
    turns = [_turn("prospect", 0.0, 5.0, "We currently use Gong for call recording")]
    t = _transcript(turns, duration_seconds=5.0)
    found = detect_competitors(t, ["Gong", "Chorus"])
    assert found == ["Gong"]


def test_competitor_detected_case_insensitive():
    turns = [_turn("prospect", 0.0, 5.0, "we tried gong last year")]
    t = _transcript(turns, duration_seconds=5.0)
    found = detect_competitors(t, ["Gong"])
    assert found == ["Gong"]


def test_competitor_not_detected():
    turns = [_turn("prospect", 0.0, 5.0, "we don't use any call recording tool")]
    t = _transcript(turns, duration_seconds=5.0)
    found = detect_competitors(t, ["Gong", "Chorus"])
    assert found == []


def test_objections_raised_regex_match():
    turns = [_turn("prospect", 0.0, 5.0, "honestly it's too expensive for us right now")]
    t = _transcript(turns, duration_seconds=5.0)
    metrics = compute_metrics(t, MetricsConfig())
    assert metrics.objections_raised == 1


def test_objections_raised_no_match():
    turns = [_turn("prospect", 0.0, 5.0, "this all sounds great to me")]
    t = _transcript(turns, duration_seconds=5.0)
    metrics = compute_metrics(t, MetricsConfig())
    assert metrics.objections_raised == 0


def test_full_compute_metrics_returns_correct_types(sample_transcript):
    metrics = compute_metrics(
        sample_transcript,
        MetricsConfig(competitor_names=["Gong", "Chorus"]),
    )
    assert isinstance(metrics, ComputedMetrics)
    assert isinstance(metrics.talk_ratio, float)
    assert isinstance(metrics.next_step_confirmed, bool)
    assert isinstance(metrics.competitor_mentions, list)
    assert isinstance(metrics.objections_raised, int)
    assert isinstance(metrics.call_duration_seconds, float)
