"""
transcript/serialiser.py

Serialisation and deserialisation for the Transcript model.

Handles three representations:
  - JSON dict  (for API responses and Celery task payloads)
  - DB row     (via SQLAlchemy models in models/transcript.py)
  - Prompt str (for the scoring engine LLM call)

Interface:
    to_json(transcript) -> dict
    from_json(data) -> Transcript
    to_db(transcript, session) -> None
    from_db(call_id, session) -> Transcript | None
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Transcript


def to_json(transcript: Transcript) -> dict:
    """
    Serialise a Transcript to a JSON-serialisable dict.
    Used in Celery task payloads and API responses.

    Args:
        transcript: The Transcript to serialise.

    Returns:
        Dict with all Transcript fields, turns, and words.
    """
    raise NotImplementedError


def from_json(data: dict) -> Transcript:
    """
    Deserialise a Transcript from a dict (e.g. from a Celery task payload).

    Args:
        data: Previously serialised by to_json().

    Returns:
        Reconstructed Transcript.
    """
    raise NotImplementedError


async def to_db(transcript: Transcript, session: AsyncSession) -> None:
    """
    Persist a Transcript and its Turns/Words to PostgreSQL.
    Upserts by call_id — safe to call multiple times.

    Args:
        transcript: Transcript to persist.
        session: Active async SQLAlchemy session.
    """
    raise NotImplementedError


async def from_db(call_id: UUID, session: AsyncSession) -> Transcript | None:
    """
    Load a Transcript from PostgreSQL by call_id.

    Args:
        call_id: UUID of the call.
        session: Active async SQLAlchemy session.

    Returns:
        Transcript if found, None otherwise.
    """
    raise NotImplementedError
