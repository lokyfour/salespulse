"""
coaching/report_builder.py

Assembles a CoachingReport from rep history and detected patterns.

The report is stored in PostgreSQL and served via the API. It is also
the payload sent to the CRM (e.g. as a HubSpot note on the rep's contact).

Interface:
    build_rep_report(rep_id, history, flags, session) -> CoachingReport
    build_team_report(team_id, summary, session) -> TeamCoachingReport
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .aggregator import RepHistory, TeamSummary
from .pattern_detector import CoachingFlag


@dataclass
class CoachingReport:
    rep_id: str
    generated_at: datetime
    calls_analysed: int
    average_overall_score: float
    score_trend_direction: str      # "improving" | "declining" | "stable"
    flags: list[CoachingFlag]
    top_strength: str | None        # Criterion with highest average score
    top_weakness: str | None        # Criterion with lowest average score
    recommended_actions: list[str] = field(default_factory=list)


@dataclass
class TeamCoachingReport:
    team_id: str
    generated_at: datetime
    rep_count: int
    average_overall_score: float
    underperformers: list[str]       # rep_ids below threshold
    top_performers: list[str]        # rep_ids above 80
    top_objections: list[str]
    competitor_leaderboard: list[tuple[str, int]]  # (competitor, mention_count)


async def build_rep_report(
    rep_id: str,
    history: RepHistory,
    flags: list[CoachingFlag],
    session: AsyncSession,
) -> CoachingReport:
    """
    Build and persist a CoachingReport for a single rep.

    Args:
        rep_id: Internal rep identifier.
        history: Aggregated scorecard history.
        flags: Coaching flags from the pattern detector.
        session: Active async SQLAlchemy session.

    Returns:
        Persisted CoachingReport.
    """
    raise NotImplementedError


async def build_team_report(
    team_id: str,
    summary: TeamSummary,
    session: AsyncSession,
) -> TeamCoachingReport:
    """
    Build and persist a team-level coaching report.

    Args:
        team_id: Team identifier.
        summary: Aggregated team summary.
        session: Active async SQLAlchemy session.

    Returns:
        Persisted TeamCoachingReport.
    """
    raise NotImplementedError
