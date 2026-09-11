"""
tests/test_scorecard.py

Tests for scorecard fixture validity and scoring/scorecard.py's
build_scorecard (fully implemented — not a stub).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from salespulse.scoring.scorecard import build_scorecard


def _raw(criterion_id, score, evidence=None, timestamp=None, flag=None):
    return {
        "criterion_id": criterion_id,
        "score": score,
        "evidence": evidence,
        "timestamp": timestamp,
        "flag": flag,
    }


# ── Fixture sanity checks ───────────────────────────────────────────────


def test_expected_scorecard_fixture_exists():
    path = Path(__file__).parent / "fixtures" / "expected_scorecard.json"
    assert path.exists()


def test_expected_scorecard_structure():
    path = Path(__file__).parent / "fixtures" / "expected_scorecard.json"
    with open(path) as f:
        data = json.load(f)

    assert "call_id" in data
    assert "overall_score" in data
    assert 0 <= data["overall_score"] <= 100
    assert "criteria_scores" in data
    assert len(data["criteria_scores"]) > 0

    for criterion in data["criteria_scores"]:
        assert "criterion_id" in criterion
        assert "score" in criterion
        assert 0 <= criterion["score"] <= 3
        assert "weight" in criterion


def test_expected_scorecard_has_coaching_flags():
    path = Path(__file__).parent / "fixtures" / "expected_scorecard.json"
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data["coaching_flags"], list)


# ── build_scorecard: score handling ─────────────────────────────────────


def test_null_score_does_not_crash(rubric):
    raw_dict = {
        "criteria_scores": [_raw("metrics", None)],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "metrics")
    assert cs.score == 0


def test_explicit_zero_score_allowed(rubric):
    raw_dict = {
        "criteria_scores": [_raw("champion", 0, flag="not observed")],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "champion")
    assert cs.score == 0


def test_evidence_required_no_evidence_zeroes_score(rubric):
    raw_dict = {
        "criteria_scores": [_raw("metrics", 3, evidence=None)],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "metrics")
    assert cs.score == 0
    assert cs.flag == "evidence_missing"


def test_evidence_required_with_evidence_keeps_score(rubric):
    raw_dict = {
        "criteria_scores": [_raw("metrics", 3, evidence="some quote", timestamp="00:10")],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    # No transcript passed → evidence is not verified, just required-present.
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "metrics")
    assert cs.score == 3


def test_unverified_evidence_required_zeroes_score_with_transcript(rubric, sample_transcript):
    raw_dict = {
        "criteria_scores": [
            _raw("metrics", 3, evidence="fabricated quote not in the call", timestamp="00:10")
        ],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4(), transcript=sample_transcript)
    cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "metrics")
    assert cs.score == 0
    assert "evidence_unverified" in cs.flag


def test_unverified_evidence_not_required_keeps_score(rubric, sample_transcript):
    raw_dict = {
        "criteria_scores": [
            _raw("champion", 2, evidence="fabricated quote not in the call", timestamp="00:10")
        ],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4(), transcript=sample_transcript)
    cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "champion")
    assert cs.score == 2
    assert "evidence_unverified" in cs.flag


def test_missing_criterion_filled_with_zero(rubric):
    raw_dict = {
        "criteria_scores": [_raw("metrics", 2, evidence="x", timestamp="00:00")],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    champion_cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "champion")
    assert champion_cs.score == 0
    assert champion_cs.flag == "not_scored_by_llm"


def test_unknown_criterion_id_is_skipped(rubric):
    raw_dict = {
        "criteria_scores": [
            _raw("not_a_real_criterion", 3, evidence="x", timestamp="00:00"),
            _raw("metrics", 2, evidence="x", timestamp="00:00"),
        ],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    scored_ids = {cs.criterion_id for cs in scorecard.criteria_scores}
    assert "not_a_real_criterion" not in scored_ids
    assert scored_ids == {c.id for c in rubric.criteria}


def test_score_above_3_is_clamped(rubric):
    raw_dict = {
        "criteria_scores": [_raw("metrics", 7, evidence="x", timestamp="00:00")],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "metrics")
    assert cs.score == 3


def test_all_rubric_criteria_present_in_output(rubric):
    raw_dict = {
        "criteria_scores": [_raw("metrics", 2, evidence="x", timestamp="00:00")],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    scored_ids = {cs.criterion_id for cs in scorecard.criteria_scores}
    rubric_ids = {c.id for c in rubric.criteria}
    assert scored_ids == rubric_ids


# ── overall_score / coaching_flags ──────────────────────────────────────


def test_overall_score_calculation_correct(rubric):
    raw_dict = {
        "criteria_scores": [
            _raw("metrics", 2, evidence="x", timestamp="00:00"),  # weight 20
            _raw("economic_buyer", 3, evidence="x", timestamp="00:00"),  # weight 20
            _raw("decision_criteria", 1, evidence="x", timestamp="00:00"),  # weight 15
            _raw("decision_process", 2),  # weight 15
            _raw("identify_pain", 3, evidence="x", timestamp="00:00"),  # weight 15
            _raw("champion", 0),  # weight 15
        ],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    expected = round(
        (2 / 3) * 20 + (3 / 3) * 20 + (1 / 3) * 15 + (2 / 3) * 15 + (3 / 3) * 15 + (0 / 3) * 15
    )
    assert scorecard.overall_score == expected


def test_coaching_flags_generated_for_zero_scores(rubric):
    raw_dict = {
        "criteria_scores": [_raw("champion", 0, flag="not observed")],
        "conversation_metrics": {"next_step_confirmed": True},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    assert any("Champion not identified" in f for f in scorecard.coaching_flags)


def test_talk_ratio_too_high_flag(rubric):
    raw_dict = {
        "criteria_scores": [],
        "conversation_metrics": {"talk_ratio": 0.75, "next_step_confirmed": True},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    assert scorecard.conversation_metrics.talk_ratio_flag == "too_high"
    assert any("above 55%" in f for f in scorecard.coaching_flags)


def test_talk_ratio_too_low_flag(rubric):
    raw_dict = {
        "criteria_scores": [],
        "conversation_metrics": {"talk_ratio": 0.10, "next_step_confirmed": True},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    assert scorecard.conversation_metrics.talk_ratio_flag == "too_low"
    assert any("below 20%" in f for f in scorecard.coaching_flags)


def test_no_next_step_flag(rubric):
    raw_dict = {
        "criteria_scores": [],
        "conversation_metrics": {"talk_ratio": 0.4, "next_step_confirmed": False},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    assert any("No next step confirmed" in f for f in scorecard.coaching_flags)
