"""
crm/webhook.py

Generic outbound HTTP webhook adapter.

Posts a structured JSON payload to a configured URL when a call is scored.
Useful for integrating with CRMs not natively supported, or for custom
downstream workflows (Zapier, n8n, Make, internal systems).

Payload schema:
  {
    "event": "call.scored",
    "call_id": "...",
    "rep_id": "...",
    "crm_deal_id": "...",
    "overall_score": 74,
    "coaching_flags": [...],
    "scorecard_url": "https://salespulse.example.com/calls/{call_id}/scorecard",
    "timestamp": "2026-09-11T10:23:00Z"
  }

Interface:
    WebhookAdapter.push_scorecard(call_id, scorecard, crm_deal_id) -> CRMPushResult
"""

from __future__ import annotations

from uuid import UUID

from ..coaching.pattern_detector import CoachingFlag
from ..scoring.scorecard import Scorecard
from .base import CRMAdapter, CRMPushResult


class WebhookAdapter(CRMAdapter):
    """Generic outbound webhook. Retries up to 3 times on HTTP error."""

    def __init__(self, webhook_url: str, secret: str | None = None) -> None:
        """
        Args:
            webhook_url: Target URL to POST the payload to.
            secret: Optional HMAC-SHA256 secret for request signing.
                    Signature is sent in X-Salespulse-Signature header.
        """
        self._webhook_url = webhook_url
        self._secret = secret

    @property
    def adapter_name(self) -> str:
        return "webhook"

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

    def _sign_payload(self, body: bytes) -> str:
        """Compute HMAC-SHA256 signature for payload body."""
        raise NotImplementedError
