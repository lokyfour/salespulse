"""
models/scorecard.py

SQLAlchemy ORM models for Scorecard and CriterionScore.

Tables: scorecards, criterion_scores

One Scorecard per Call. One CriterionScore per rubric criterion per Call.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .call import Base


class Scorecard(Base):
    __tablename__ = "scorecards"

    scorecard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.call_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    rubric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rubric_version: Mapped[str] = mapped_column(String(50), nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Conversation metrics
    talk_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    next_step_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    objections_handled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    competitor_mentions: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )

    overall_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    criterion_scores: Mapped[list[CriterionScore]] = relationship(
        "CriterionScore", back_populates="scorecard", cascade="all, delete-orphan"
    )


class CriterionScore(Base):
    __tablename__ = "criterion_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scorecard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scorecards.scorecard_id", ondelete="CASCADE"),
        nullable=False,
    )
    criterion_id: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_timestamp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    flag: Mapped[str | None] = mapped_column(String(100), nullable=True)

    scorecard: Mapped[Scorecard] = relationship("Scorecard", back_populates="criterion_scores")
