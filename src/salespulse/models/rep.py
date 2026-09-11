"""
models/rep.py

SQLAlchemy ORM model for Rep.

The Rep row is a lightweight identity record. Detailed performance
data lives in Scorecard and CoachingReport, joined by rep_id.

Table: reps
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .call import Base


class Rep(Base):
    __tablename__ = "reps"

    rep_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    team_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # CRM identity — used by adapters to find the rep's CRM contact record
    crm_contact_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    crm_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
