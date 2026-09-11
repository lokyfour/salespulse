"""
crm/hubspot.py

HubSpot CRM adapter using the HubSpot v3 REST API.

Scorecard is written as:
  - Custom deal properties: salespulse_score, salespulse_rubric,
    salespulse_next_step, salespulse_competitors
  - Engagement (note) on the deal with full coaching flags text

Idempotency: before writing, checks for an existing engagement with
external_id = "salespulse:{call_id}". Updates if found, inserts if not.

Requires:
  HUBSPOT_API_KEY (private app token) in environment
  Custom deal properties created in HubSpot settings before first use

Interface:
    HubSpotAdapter.push_scorecard(call_id, scorecard, crm_deal_id) -> CRMPushResult
    HubSpotAdapter.push_coaching_flag(rep_id, flag) -> CRMPushResult
"""

from __future__ import annotations

from uuid import UUID

from .base import CRMAdapter, CRMPushResult
from ..scoring.scorecard import Scorecard
from ..coaching.pattern_detector import CoachingFlag


HUBSPOT_BASE_URL = "https://api.hubapi.com"


class HubSpotAdapter(CRMAdapter):
    """HubSpot v3 REST API adapter."""

    def __init__(self, api_key: str, portal_id: str) -> None:
        """
        Args:
            api_key: HubSpot private app token.
            portal_id: HubSpot portal (account) ID.
        """
        self._api_key = api_key
        self._portal_id = portal_id

    @property
    def adapter_name(self) -> str:
        return "hubspot"

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

    async def _upsert_deal_properties(
        self,
        deal_id: str,
        properties: dict,
    ) -> str:
        """PATCH deal properties. Return deal_id."""
        raise NotImplementedError

    async def _create_engagement_note(
        self,
        deal_id: str,
        body: str,
        external_id: str,
    ) -> str:
        """Create or update a note engagement. Return engagement_id."""
        raise NotImplementedError
