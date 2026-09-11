"""
crm/pipedrive.py

Pipedrive CRM adapter using the Pipedrive REST API v1.

Scorecard is written as:
  - Activity (type: call) on the deal with score and flags in note field
  - Custom deal field update: salespulse_score

Idempotency: activities are tagged with subject="salespulse:{call_id}".
Existing activities with matching subject are updated, not duplicated.

Interface:
    PipedriveAdapter.push_scorecard(call_id, scorecard, crm_deal_id) -> CRMPushResult
    PipedriveAdapter.push_coaching_flag(rep_id, flag) -> CRMPushResult
"""

from __future__ import annotations

from uuid import UUID

from .base import CRMAdapter, CRMPushResult
from ..scoring.scorecard import Scorecard
from ..coaching.pattern_detector import CoachingFlag


PIPEDRIVE_BASE_URL = "https://{domain}.pipedrive.com/v1"


class PipedriveAdapter(CRMAdapter):
    """Pipedrive v1 REST API adapter."""

    def __init__(self, api_token: str, domain: str) -> None:
        """
        Args:
            api_token: Pipedrive API token.
            domain: Pipedrive company domain (subdomain of pipedrive.com).
        """
        self._api_token = api_token
        self._base_url = PIPEDRIVE_BASE_URL.format(domain=domain)

    @property
    def adapter_name(self) -> str:
        return "pipedrive"

    async def push_scorecard(
        self,
        call_id: UUID,
        scorecard: Scorecard,
        crm_deal_id: str | None,
    ) -> CRMPushResult:
        raise NotImplementedError

    async def push_coaching_flag(
        self,
        rep_id: str,
        flag: CoachingFlag,
    ) -> CRMPushResult:
        raise NotImplementedError
