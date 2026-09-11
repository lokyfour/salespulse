"""
scoring/rubric.py

Loads and validates the scoring rubric from config/rubric.yaml.

The rubric defines:
  - Methodology name (meddic | bant | custom)
  - Criteria: id, label, weight, description, scoring_guide, evidence_required
  - Conversation metrics: talk_ratio bounds, next_step, competitor detection

RubricConfig is passed to the prompt builder and scoring engine.
Changing the rubric requires only a config edit, not code changes.

Interface:
    load_rubric(path: Path) -> RubricConfig
    RubricConfig.total_weight_valid() -> bool  # weights must sum to 100
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScoringGuide:
    """Maps integer score levels to plain-English descriptions."""
    level_0: str
    level_1: str
    level_2: str
    level_3: str


@dataclass
class Criterion:
    id: str
    label: str
    weight: int                     # Percentage of overall score (0–100)
    description: str
    evidence_required: bool
    scoring_guide: ScoringGuide


@dataclass
class ConversationMetric:
    id: str
    label: str
    type: str                       # "range" | "boolean" | "count" | "list"
    target_range: tuple[float, float] | None = None
    flag_above: float | None = None
    flag_below: float | None = None
    description: str = ""


@dataclass
class RubricConfig:
    name: str
    methodology: str                # "meddic" | "bant" | "custom"
    version: str
    criteria: list[Criterion] = field(default_factory=list)
    conversation_metrics: list[ConversationMetric] = field(default_factory=list)

    def total_weight_valid(self) -> bool:
        """Criterion weights must sum to exactly 100."""
        return sum(c.weight for c in self.criteria) == 100

    def criterion_by_id(self, criterion_id: str) -> Criterion | None:
        """Return the criterion with the given id, or None."""
        for c in self.criteria:
            if c.id == criterion_id:
                return c
        return None


def load_rubric(path: Path) -> RubricConfig:
    """
    Parse `path` (rubric.yaml) and return a validated RubricConfig.

    Args:
        path: Path to the rubric YAML file.

    Returns:
        Validated RubricConfig.

    Raises:
        ValueError: If weights != 100 or required fields missing.
        FileNotFoundError: If path does not exist.
    """
    import yaml

    if not path.exists():
        raise FileNotFoundError(f"Rubric not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    raw = data.get("rubric", data)

    criteria: list[Criterion] = []
    for c in raw.get("criteria", []):
        sg = c.get("scoring_guide", {})
        # YAML keys may be ints or strings depending on quoting
        def sg_level(level: int) -> str:
            return str(sg.get(level, sg.get(str(level), "")))

        criteria.append(Criterion(
            id=c["id"],
            label=c["label"],
            weight=int(c["weight"]),
            description=str(c.get("description", "")).strip(),
            evidence_required=bool(c.get("evidence_required", False)),
            scoring_guide=ScoringGuide(
                level_0=sg_level(0),
                level_1=sg_level(1),
                level_2=sg_level(2),
                level_3=sg_level(3),
            ),
        ))

    metrics: list[ConversationMetric] = []
    for m in raw.get("conversation_metrics", []):
        tr = m.get("target_range")
        metrics.append(ConversationMetric(
            id=m["id"],
            label=m.get("label", m["id"]),
            type=m.get("type", "count"),
            target_range=tuple(tr) if tr else None,
            flag_above=m.get("flag_above"),
            flag_below=m.get("flag_below"),
            description=str(m.get("description", "")).strip(),
        ))

    rubric = RubricConfig(
        name=raw.get("name", "Custom"),
        methodology=raw.get("methodology", "custom"),
        version=str(raw.get("version", "1.0")),
        criteria=criteria,
        conversation_metrics=metrics,
    )

    if not rubric.total_weight_valid():
        total = sum(c.weight for c in rubric.criteria)
        raise ValueError(f"Criterion weights sum to {total}, must equal 100.")

    return rubric
