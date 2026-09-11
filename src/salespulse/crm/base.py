"""
crm/base.py

Abstract base class for CRM adapters.

All writes are idempotent — re-submitting the same call_id must not
create duplicate records, notes, or tasks in the CRM.

Concrete adapters:
  - HubSpotAdapter      (HubSpot v3 REST API)
  - SalesforceAdapter   (Salesforce REST API, OAuth2 PKCE)
  - PipedriveAdapter    (Pipedrive v1 REST API)
  - WebhookAdapter      (Generic outbound HTTP webhook)

Interface:
    CRMAdapter.push_scorecard(call_id, scorecard, session) -> CRMPushResult
    CRMAdapter.push_coaching_flag(rep_id, flag, session) -> CRMPushResult
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from ..coaching.pattern_detector import CoachingFlag
from ..scoring.scorecard import Scorecard


@dataclass
class CRMPushResult:
    success: bool
    crm_record_id: str | None  # ID of created/updated CRM record
    error_message: str | None  # None on success


class CRMAdapter(ABC):
    """
    Push scorecard results and coaching flags to a CRM.

    Implementations must handle authentication, rate limiting, and
    idempotency internally. The pipeline treats all writes as fire-and-forget
    (retried by Celery on failure, not blocking the scorecard result).
    """

    @abstractmethod
    async def push_scorecard(
        self,
        call_id: UUID,
        scorecard: Scorecard,
        crm_deal_id: str | None,
    ) -> CRMPushResult:
        """
        Write the scorecard result to the associated CRM deal or contact.

        What gets written varies by CRM, but typically includes:
          - Overall score as a custom field
          - Coaching flags as a deal note or activity
          - Next step confirmation status
          - Competitor mentions

        Args:
            call_id: Pipeline call UUID (used as external key for idempotency).
            scorecard: Completed scorecard.
            crm_deal_id: CRM-side deal or contact ID, if known.

        Returns:
            CRMPushResult.
        """
        raise NotImplementedError

    @abstractmethod
    async def push_coaching_flag(
        self,
        rep_id: str,
        flag: CoachingFlag,
    ) -> CRMPushResult:
        """
        Create a coaching task or note on the rep's CRM contact record.

        Args:
            rep_id: Internal rep identifier (mapped to CRM contact).
            flag: Coaching flag to persist.

        Returns:
            CRMPushResult.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Short identifier used in logs."""
        raise NotImplementedError


class CRMError(Exception):
    """Raised when a CRM push fails after retries."""

    pass
