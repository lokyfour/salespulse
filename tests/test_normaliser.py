"""
tests/test_normaliser.py

Unit tests for transcript/normaliser.py's normalise_from_fixture.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from salespulse.transcript.models import Transcript
from salespulse.transcript.normaliser import normalise_from_fixture

FIXTURE = Path(__file__).parent / "fixtures" / "sample_transcript.json"


def test_normalise_from_fixture_returns_transcript():
    t = normalise_from_fixture(FIXTURE, uuid.uuid4())
    assert isinstance(t, Transcript)


def test_normalise_from_fixture_turn_count():
    t = normalise_from_fixture(FIXTURE, uuid.uuid4())
    assert len(t.turns) == 11


def test_normalise_from_fixture_rep_turns():
    t = normalise_from_fixture(FIXTURE, uuid.uuid4())
    assert len(t.rep_turns) == 6
    assert all(turn.speaker == "rep" for turn in t.rep_turns)


def test_normalise_from_fixture_prospect_turns():
    t = normalise_from_fixture(FIXTURE, uuid.uuid4())
    assert len(t.prospect_turns) == 5
    assert all(turn.speaker != "rep" for turn in t.prospect_turns)


def test_normalise_from_fixture_duration():
    t = normalise_from_fixture(FIXTURE, uuid.uuid4())
    assert t.duration_seconds == 183.4


def test_as_prompt_string_format():
    t = normalise_from_fixture(FIXTURE, uuid.uuid4())
    rendered = t.as_prompt_string()
    assert "[00:02] REP:" in rendered
    assert "PROSPECT:" in rendered
    for line in rendered.splitlines():
        assert line.startswith("[")
        assert "] " in line


def test_rep_talk_ratio_in_range():
    t = normalise_from_fixture(FIXTURE, uuid.uuid4())
    assert 0.0 <= t.rep_talk_ratio <= 1.0


def test_missing_fixture_raises():
    with pytest.raises(FileNotFoundError):
        normalise_from_fixture(Path("tests/fixtures/does_not_exist.json"), uuid.uuid4())
