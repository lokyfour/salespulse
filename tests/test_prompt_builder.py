"""
tests/test_prompt_builder.py

Unit tests for scoring/prompt_builder.py.
"""

from __future__ import annotations

from salespulse.scoring.prompt_builder import build_prompt


def test_system_prompt_not_empty(sample_transcript, rubric):
    system_prompt, _ = build_prompt(sample_transcript, rubric)
    assert isinstance(system_prompt, str)
    assert len(system_prompt.strip()) > 0


def test_user_prompt_contains_transcript(sample_transcript, rubric):
    _, user_prompt = build_prompt(sample_transcript, rubric)
    assert sample_transcript.as_prompt_string() in user_prompt


def test_user_prompt_contains_all_criteria_ids(sample_transcript, rubric):
    _, user_prompt = build_prompt(sample_transcript, rubric)
    for c in rubric.criteria:
        assert c.label in user_prompt


def test_user_prompt_contains_weights(sample_transcript, rubric):
    _, user_prompt = build_prompt(sample_transcript, rubric)
    for c in rubric.criteria:
        assert f"weight: {c.weight}%" in user_prompt


def test_evidence_required_marked_in_prompt(sample_transcript, rubric):
    _, user_prompt = build_prompt(sample_transcript, rubric)
    required_labels = [c.label for c in rubric.criteria if c.evidence_required]
    assert required_labels, "fixture rubric should have at least one evidence_required criterion"
    for label in required_labels:
        idx = user_prompt.index(label)
        line = user_prompt[idx: idx + 200].splitlines()[0]
        assert "[EVIDENCE REQUIRED]" in line


def test_prompt_includes_json_format_instructions(sample_transcript, rubric):
    _, user_prompt = build_prompt(sample_transcript, rubric)
    assert "criteria_scores" in user_prompt
    assert "conversation_metrics" in user_prompt
    assert "overall_notes" in user_prompt
