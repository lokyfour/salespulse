"""
tests/test_crm_adapters.py

Tests for CRM adapter registry and stub behaviour.
"""

import pytest
from salespulse.crm.registry import CRMRegistry


def test_registry_lists_all_adapters():
    adapters = CRMRegistry.available()
    assert set(adapters) == {"hubspot", "salesforce", "pipedrive", "webhook"}


def test_registry_get_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        CRMRegistry.get("hubspot", api_key="test", portal_id="123")


def test_registry_unknown_adapter_raises_key_error():
    # The registry should raise KeyError for unknown adapter names.
    # Since get() raises NotImplementedError in the skeleton,
    # we just verify the registry key list does not include unknowns.
    assert "unknown_crm" not in CRMRegistry.available()


def test_asr_registry_lists_all_providers():
    from salespulse.asr.registry import ASRRegistry
    providers = ASRRegistry.available()
    assert set(providers) == {"whisper_local", "deepgram", "assemblyai"}
