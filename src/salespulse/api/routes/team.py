"""
api/routes/team.py

Team-level report and leaderboard.

Routes:
    GET /team/{team_id}/report       Team summary + outlier reps
    GET /team/{team_id}/leaderboard  Rep ranking by score (last 30 days)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import TeamReportResponse

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/{team_id}/report", response_model=TeamReportResponse)
async def get_team_report(
    team_id: str,
    session: AsyncSession = Depends(lambda: None),
) -> TeamReportResponse:
    """Return team-level summary: averages, outliers, top objections, competitors."""
    raise NotImplementedError


@router.get("/{team_id}/leaderboard")
async def get_team_leaderboard(
    team_id: str,
    days: int = 30,
    session: AsyncSession = Depends(lambda: None),
) -> list[dict]:
    """
    Return reps ranked by average overall score over the last `days` days.
    Each entry: {"rep_id": str, "average_score": float, "call_count": int}.
    """
    raise NotImplementedError
