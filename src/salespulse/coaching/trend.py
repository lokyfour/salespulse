"""
coaching/trend.py

Week-over-week and call-over-call trend computation for rep scores.

Trend is expressed as a direction (improving/declining/stable) and a
delta value (change in overall score per call, linear regression slope).

Used in CoachingReport.score_trend_direction and the rep dashboard sparkline.

Interface:
    compute_trend(scores: list[float]) -> TrendResult
    compute_weekly_deltas(scorecards_by_week) -> list[WeeklyDelta]
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrendResult:
    direction: str       # "improving" | "declining" | "stable"
    slope: float         # Points per call (linear regression)
    r_squared: float     # Fit quality 0.0 – 1.0; low = noisy


@dataclass
class WeeklyDelta:
    week_label: str      # e.g. "2026-W36"
    average_score: float
    call_count: int
    delta_from_prior: float | None  # None for first week


def compute_trend(scores: list[float]) -> TrendResult:
    """
    Fit a linear regression to `scores` (ordered oldest → newest) and
    classify the slope.

    Thresholds:
      slope > +0.5 points/call  → "improving"
      slope < -0.5 points/call  → "declining"
      otherwise                 → "stable"

    Args:
        scores: Ordered list of overall scores (0–100).

    Returns:
        TrendResult with direction, slope, and R².

    Raises:
        ValueError: If fewer than 3 scores provided (trend undefined).
    """
    raise NotImplementedError


def compute_weekly_deltas(
    scorecards_by_week: dict[str, list[float]],
) -> list[WeeklyDelta]:
    """
    Compute week-over-week score changes.

    Args:
        scorecards_by_week: Dict mapping ISO week label to list of scores
                            for that week, sorted chronologically.

    Returns:
        List of WeeklyDelta sorted by week_label ascending.
    """
    raise NotImplementedError
