"""
coaching/pattern_detector.py

Detects actionable coaching patterns from aggregated rep history.

Patterns detected:
  - Criterion consistently below threshold (rep weakness)
  - Talk ratio chronically above/below optimal range
  - Next step not confirmed on > 40% of calls
  - Same objection appearing in > 50% of recent calls (unaddressed)
  - Score declining trend over last 5 calls

Each pattern produces a CoachingFlag with a severity and a plain-English
recommendation. Flags with min_calls_for_pattern calls are suppressed to
avoid false positives on reps with thin history.

Interface:
    detect_patterns(history, config) -> list[CoachingFlag]
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .aggregator import RepHistory


class FlagSeverity(str, Enum):
    INFO = "info"       # Observation, no action required
    WARN = "warn"       # Worth a 1:1 conversation
    CRITICAL = "critical"  # Manager review recommended


@dataclass
class CoachingFlag:
    severity: FlagSeverity
    criterion_id: str | None   # Which criterion, if applicable
    title: str                 # Short flag title
    recommendation: str        # Actionable plain-English coaching tip
    evidence_summary: str      # e.g. "Missed on 7 of last 10 calls"


@dataclass
class PatternConfig:
    min_calls_for_pattern: int = 5
    criterion_weak_threshold: float = 1.0   # Average score below this
    underperformer_overall_threshold: int = 55
    next_step_miss_rate_threshold: float = 0.40
    talk_ratio_min: float = 0.38
    talk_ratio_max: float = 0.55
    objection_repeat_threshold: float = 0.50


def detect_patterns(
    history: RepHistory,
    config: PatternConfig,
) -> list[CoachingFlag]:
    """
    Analyse rep history and return coaching flags sorted by severity.

    Args:
        history: Aggregated rep scorecard history.
        config: Detection thresholds.

    Returns:
        List of CoachingFlag sorted by severity (CRITICAL first).
    """
    raise NotImplementedError
