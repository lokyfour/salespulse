"""
models/call.py

SQLAlchemy ORM model for a call record.

The Call row is the root entity. All other models (Transcript, Scorecard,
CoachingReport) reference it by call_id (UUID primary key).

Table: calls
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Call(Base):
    """Root entity for a processed sales call."""

    __tablename__ = "calls"

    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rep_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    team_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    crm_deal_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    crm_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Pipeline state
    stage: Mapped[str] = mapped_column(
        String(50), nullable=False, default="queued", index=True
    )
    failed_at_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Audio metadata
    audio_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    audio_duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    asr_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # GDPR erasure flag
    erased_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
