"""
crm/salesforce.py

Salesforce CRM adapter using the Salesforce REST API (v59+).

Authentication: OAuth2 client credentials (connected app) — not username/password.
Idempotency: upsert by ExternalId__c = "salespulse:{call_id}" on a custom
SalesCallScore__c object.

Custom objects/fields required in the Salesforce org:
  SalesCallScore__c — custom object with:
    ExternalId__c      (Text, External ID)
    DealId__c          (Text)
    OverallScore__c    (Number)
    CoachingFlags__c   (Long Text Area)
    NextStepConfirmed__c (Checkbox)

Interface:
    SalesforceAdapter.push_scorecard(call_id, scorecard, crm_deal_id) -> CRMPushResult
    SalesforceAdapter.push_coaching_flag(rep_id, flag) -> CRMPushResult
"""

from __future__ import annotations

from uuid import UUID

from .base import CRMAdapter, CRMPushResult
from ..scoring.scorecard import Scorecard
from ..coaching.pattern_detector import CoachingFlag


class SalesforceAdapter(CRMAdapter):
    """Salesforce REST API adapter with OAuth2 client credentials."""

    def __init__(
        self,
        instance_url: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        """
        Args:
            instance_url: Salesforce instance URL (e.g. https://myorg.my.salesforce.com).
            client_id: Connected app consumer key.
            client_secret: Connected app consumer secret.
        """
        self._instance_url = instance_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token: str | None = None

    @property
    def adapter_name(self) -> str:
        return "salesforce"

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

    async def _authenticate(self) -> str:
        """Obtain access token via client credentials flow. Cache until expiry."""
        raise NotImplementedError

    async def _upsert_call_score(
        self,
        external_id: str,
        payload: dict,
    ) -> str:
        """Upsert SalesCallScore__c by ExternalId__c. Return record ID."""
        raise NotImplementedError
