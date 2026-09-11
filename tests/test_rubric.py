"""
tests/test_rubric.py

Tests for rubric loading and validation (scoring/rubric.py).

load_rubric is fully implemented (not a stub), so these tests exercise
real parsing/validation behaviour against config/rubric.example.yaml and
hand-built temporary YAML files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from salespulse.scoring.rubric import RubricConfig, load_rubric

RUBRIC_PATH = Path(__file__).parent.parent / "config" / "rubric.example.yaml"


def test_rubric_example_file_exists():
    assert RUBRIC_PATH.exists(), "config/rubric.example.yaml must exist"


def test_rubric_example_is_valid_yaml():
    import yaml

    with open(RUBRIC_PATH) as f:
        data = yaml.safe_load(f)
    assert "rubric" in data
    assert "criteria" in data["rubric"]
    assert len(data["rubric"]["criteria"]) > 0


def test_rubric_weights_sum_to_100():
    import yaml

    with open(RUBRIC_PATH) as f:
        data = yaml.safe_load(f)
    total = sum(c["weight"] for c in data["rubric"]["criteria"])
    assert total == 100, f"Criterion weights sum to {total}, expected 100"


def test_load_rubric_valid_file():
    rubric = load_rubric(RUBRIC_PATH)
    assert isinstance(rubric, RubricConfig)
    assert rubric.name == "MEDDIC Enterprise"
    assert rubric.methodology == "meddic"


def test_load_rubric_weights_not_100_raises(tmp_path):
    bad_yaml = tmp_path / "bad_rubric.yaml"
    bad_yaml.write_text(
        """
rubric:
  name: "Bad"
  methodology: "custom"
  version: "1.0"
  criteria:
    - id: a
      label: "A"
      weight: 50
      description: "d"
      evidence_required: false
      scoring_guide: {0: "x", 1: "x", 2: "x", 3: "x"}
"""
    )
    with pytest.raises(ValueError):
        load_rubric(bad_yaml)


def test_load_rubric_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_rubric(Path("config/does_not_exist.yaml"))


def test_load_rubric_criteria_count():
    rubric = load_rubric(RUBRIC_PATH)
    assert len(rubric.criteria) == 6


def test_criterion_by_id_found():
    rubric = load_rubric(RUBRIC_PATH)
    criterion = rubric.criterion_by_id("metrics")
    assert criterion is not None
    assert criterion.label == "Metrics"


def test_criterion_by_id_not_found():
    rubric = load_rubric(RUBRIC_PATH)
    assert rubric.criterion_by_id("does_not_exist") is None


def test_rubric_total_weight_valid_true():
    rubric = load_rubric(RUBRIC_PATH)
    assert rubric.total_weight_valid() is True


def test_rubric_total_weight_valid_false():
    rubric = RubricConfig(
        name="test",
        methodology="custom",
        version="1.0",
        criteria=[],
    )
    from salespulse.scoring.rubric import Criterion, ScoringGuide

    rubric.criteria.append(
        Criterion(
            id="only",
            label="Only",
            weight=50,
            description="",
            evidence_required=False,
            scoring_guide=ScoringGuide(level_0="", level_1="", level_2="", level_3=""),
        )
    )
    assert rubric.total_weight_valid() is False
