"""
coaching/aggregator.py

Aggregates scorecard history for a rep or team to surface patterns.

Aggregation windows:
  - Last N calls (default: 10)
  - Last 30 days
  - Current week vs previous week

Output feeds the pattern detector and report builder.

Interface:
    RepAggregator.get_history(rep_id, window, session) -> RepHistory
    TeamAggregator.get_summary(team_id, window, session) -> TeamSummary
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..scoring.scorecard import Scorecard


@dataclass
class AggregationWindow:
    last_n_calls: int | None = 10
    since_date: date | None = None


@dataclass
class RepHistory:
    rep_id: str
    scorecards: list[Scorecard]
    average_overall_score: float
    score_trend: float          # Positive = improving, negative = declining
    per_criterion_averages: dict[str, float] = field(default_factory=dict)
    most_missed_criterion: str | None = None
    top_objections: list[str] = field(default_factory=list)


@dataclass
class TeamSummary:
    team_id: str
    rep_count: int
    average_overall_score: float
    underperformer_rep_ids: list[str] = field(default_factory=list)
    top_performer_rep_ids: list[str] = field(default_factory=list)
    team_top_objections: list[str] = field(default_factory=list)
    competitor_frequency: dict[str, int] = field(default_factory=dict)


class RepAggregator:
    """Aggregates a single rep's scoring history."""

    async def get_history(
        self,
        rep_id: str,
        window: AggregationWindow,
        session: AsyncSession,
    ) -> RepHistory:
        """
        Fetch and aggregate a rep's scorecards from PostgreSQL.

        Args:
            rep_id: Internal rep identifier.
            window: Aggregation window (last N calls or since date).
            session: Active async SQLAlchemy session.

        Returns:
            RepHistory with averages, trends, and top patterns.
        """
        raise NotImplementedError


class TeamAggregator:
    """Aggregates scorecards across all reps on a team."""

    async def get_summary(
        self,
        team_id: str,
        window: AggregationWindow,
        session: AsyncSession,
    ) -> TeamSummary:
        """
        Aggregate scorecards for all reps in `team_id`.

        Args:
            team_id: Team identifier.
            window: Aggregation window.
            session: Active async SQLAlchemy session.

        Returns:
            TeamSummary with cross-rep patterns and outliers.
        """
        raise NotImplementedError
