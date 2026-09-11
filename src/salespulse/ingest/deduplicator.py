"""
ingest/deduplicator.py

Prevents the same call from entering the pipeline more than once.

Deduplication keys by source:
  - File upload:      SHA-256 of the audio file content
  - CRM webhook:      (crm_type, crm_deal_id)
  - Twilio:           recording_sid

Interface:
    Deduplicator.is_duplicate(key: str, session) -> bool
    Deduplicator.register(key: str, call_id: UUID, session) -> None
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class Deduplicator:
    """
    Checks and registers deduplication keys in the `call_dedup_keys`
    table. All operations are idempotent.
    """

    async def is_duplicate(
        self,
        key: str,
        session: AsyncSession,
    ) -> bool:
        """
        Return True if `key` has already been processed.

        Args:
            key: Deduplication key (file hash, CRM deal ID, etc.).
            session: Active async SQLAlchemy session.
        """
        raise NotImplementedError

    async def register(
        self,
        key: str,
        call_id: UUID,
        session: AsyncSession,
    ) -> None:
        """
        Persist a dedup key → call_id mapping.
        No-op if the key already exists (idempotent).

        Args:
            key: Deduplication key.
            call_id: Call UUID assigned to this recording.
            session: Active async SQLAlchemy session.
        """
        raise NotImplementedError
