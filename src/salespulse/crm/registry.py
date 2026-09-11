"""
crm/registry.py

CRM adapter registry — resolves config key to a CRMAdapter instance.

Usage:
    adapter = CRMRegistry.get("hubspot", api_key="...", portal_id="...")
    await adapter.push_scorecard(call_id, scorecard, deal_id)

Registered adapters:
    "hubspot"     → HubSpotAdapter
    "salesforce"  → SalesforceAdapter
    "pipedrive"   → PipedriveAdapter
    "webhook"     → WebhookAdapter
"""

from __future__ import annotations

from typing import Any

from .base import CRMAdapter
from .hubspot import HubSpotAdapter
from .pipedrive import PipedriveAdapter
from .salesforce import SalesforceAdapter
from .webhook import WebhookAdapter

_REGISTRY: dict[str, type[CRMAdapter]] = {
    "hubspot": HubSpotAdapter,
    "salesforce": SalesforceAdapter,
    "pipedrive": PipedriveAdapter,
    "webhook": WebhookAdapter,
}


class CRMRegistry:
    """Factory for CRM adapters. Keyed by the `crm.adapter` config value."""

    @staticmethod
    def get(adapter_name: str, **kwargs: Any) -> CRMAdapter:
        """
        Return an instantiated CRM adapter.

        Args:
            adapter_name: Registry key (e.g. "hubspot").
            **kwargs: Constructor arguments forwarded to the adapter class.

        Returns:
            Concrete CRMAdapter instance.

        Raises:
            KeyError: If `adapter_name` is not registered.
        """
        raise NotImplementedError

    @staticmethod
    def available() -> list[str]:
        """Return the list of registered adapter names."""
        return list(_REGISTRY.keys())
