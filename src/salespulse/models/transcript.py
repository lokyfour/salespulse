"""
models/transcript.py

SQLAlchemy ORM models for Transcript and Turn.

Tables: transcripts, turns

One Transcript per Call. One Turn per speaker turn in the conversation.
Words are stored as JSONB inside the Turn row (not a separate table)
to avoid 10 000-row fan-out for long calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .call import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    transcript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.call_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    asr_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    rep_speaker_id: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    turns: Mapped[list[Turn]] = relationship(
        "Turn",
        back_populates="transcript",
        order_by="Turn.position",
        cascade="all, delete-orphan",
    )


class Turn(Base):
    __tablename__ = "turns"

    turn_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transcript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcripts.transcript_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # order in transcript
    speaker: Mapped[str] = mapped_column(String(100), nullable=False)  # "rep" | "prospect"
    start: Mapped[float] = mapped_column(Float, nullable=False)
    end: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Words stored as [{word, start, end, confidence}] — avoids O(N) join
    words: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    transcript: Mapped[Transcript] = relationship("Transcript", back_populates="turns")
