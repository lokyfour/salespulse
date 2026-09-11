"""
api/routes/webhooks.py

Inbound webhook verification utilities shared across CRM webhook handlers.

Provides:
    verify_hubspot_signature(request) -> bool
    verify_twilio_signature(request, auth_token) -> bool

These are called by the route handlers in calls.py before processing
the payload. Invalid signatures return 403 immediately.
"""

from __future__ import annotations

from fastapi import Request


async def verify_hubspot_signature(request: Request, client_secret: str) -> bool:
    """
    Verify HubSpot webhook signature (v3 SHA-256 HMAC).

    Header: X-HubSpot-Signature-v3
    https://developers.hubspot.com/docs/api/webhooks/validating-requests

    Args:
        request: Incoming FastAPI request.
        client_secret: HubSpot app client secret.

    Returns:
        True if signature is valid.
    """
    raise NotImplementedError


async def verify_twilio_signature(request: Request, auth_token: str) -> bool:
    """
    Verify Twilio request signature using Twilio's HMAC-SHA1 scheme.

    Header: X-Twilio-Signature
    https://www.twilio.com/docs/usage/security

    Args:
        request: Incoming FastAPI request.
        auth_token: Twilio account auth token.

    Returns:
        True if signature is valid.
    """
    raise NotImplementedError
