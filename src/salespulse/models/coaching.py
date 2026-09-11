"""
models/coaching.py

SQLAlchemy ORM model for CoachingReport.

One CoachingReport per rep, updated (upserted) after every scored call.
Stores the latest aggregated pattern analysis and coaching flags.

Table: coaching_reports
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .call import Base


class CoachingReport(Base):
    __tablename__ = "coaching_reports"

    rep_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    calls_analysed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_trend_direction: Mapped[str] = mapped_column(
        String(20), nullable=False, default="stable"
    )  # "improving" | "declining" | "stable"

    top_strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    top_weakness: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Serialised list of CoachingFlag dicts
    flags: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Serialised list of plain-English action strings
    recommended_actions: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
