"""
tests/test_scorecard_bugs.py

Focused regression tests for scorecard bugs #3 and #4:
  - null "score" from the LLM must not crash build_scorecard
  - unverified evidence on an evidence_required criterion must zero the
    score; on a non-required criterion it must only flag, not zero.

No LLM is called — raw_dict inputs are crafted by hand.
"""

from __future__ import annotations

import uuid

from salespulse.scoring.scorecard import build_scorecard


def _raw(criterion_id, score, evidence=None, timestamp=None, flag=None):
    return {
        "criterion_id": criterion_id,
        "score": score,
        "evidence": evidence,
        "timestamp": timestamp,
        "flag": flag,
    }


def test_null_score_does_not_crash(rubric):
    raw_dict = {
        "criteria_scores": [_raw("metrics", None, evidence="anything", timestamp="00:00")],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    metrics_cs = next(cs for cs in scorecard.criteria_scores if cs.criterion_id == "metrics")
    assert metrics_cs.score == 0


def test_unverified_evidence_required_zeroes_score(rubric, sample_transcript):
    # "metrics" is evidence_required=True; the quote below does not appear
    # anywhere in sample_transcript.json.
    raw_dict = {
        "criteria_scores": [
            _raw(
                "metrics",
                3,
                evidence="This sentence was never spoken on this call at all.",
                timestamp="00:15",
            )
        ],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4(), transcript=sample_transcript)
    metrics_cs = next(cs for cs in scorecard.criteria_scores if cs.criterion_id == "metrics")
    assert metrics_cs.score == 0
    assert metrics_cs.flag is not None and "evidence_unverified" in metrics_cs.flag


def test_unverified_evidence_not_required_keeps_score(rubric, sample_transcript):
    # "champion" is evidence_required=False; an unverified quote should only
    # flag, not zero, the score.
    raw_dict = {
        "criteria_scores": [
            _raw(
                "champion",
                2,
                evidence="This sentence was never spoken on this call at all.",
                timestamp="00:15",
            )
        ],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4(), transcript=sample_transcript)
    champion_cs = next(cs for cs in scorecard.criteria_scores if cs.criterion_id == "champion")
    assert champion_cs.score == 2
    assert champion_cs.flag is not None and "evidence_unverified" in champion_cs.flag


def test_evidence_missing_on_required_zeroes_score(rubric):
    raw_dict = {
        "criteria_scores": [_raw("economic_buyer", 3, evidence=None, timestamp=None)],
        "conversation_metrics": {},
        "overall_notes": "",
    }
    scorecard = build_scorecard(raw_dict, rubric, uuid.uuid4())
    cs = next(c for c in scorecard.criteria_scores if c.criterion_id == "economic_buyer")
    assert cs.score == 0
    assert cs.flag == "evidence_missing"


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
