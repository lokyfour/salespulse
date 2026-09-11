"""
api/routes/reps.py

Per-rep dashboard and coaching endpoints.

Routes:
    GET /reps/{rep_id}/dashboard   Scorecard history + trend
    GET /reps/{rep_id}/coaching    Coaching report with flags
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import CoachingFlagResponse, RepDashboardResponse

router = APIRouter(prefix="/reps", tags=["reps"])


@router.get("/{rep_id}/dashboard", response_model=RepDashboardResponse)
async def get_rep_dashboard(
    rep_id: str,
    last_n_calls: int = 10,
    session: AsyncSession = Depends(lambda: None),
) -> RepDashboardResponse:
    """Return a rep's recent scorecard history, trend, and top coaching flags."""
    raise NotImplementedError


@router.get("/{rep_id}/coaching", response_model=list[CoachingFlagResponse])
async def get_rep_coaching(
    rep_id: str,
    session: AsyncSession = Depends(lambda: None),
) -> list[CoachingFlagResponse]:
    """Return the current coaching flags for a rep, ordered by severity."""
    raise NotImplementedError
