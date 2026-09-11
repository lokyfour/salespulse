"""
tests/test_crm_registry.py

Tests for the CRM adapter registry and ASR provider registry.
Both .get() implementations are stubs (raise NotImplementedError) — the
scoring/pipeline code that calls them (pipeline/tasks.py::push_to_crm)
is responsible for catching that and degrading gracefully (see
tests/test_pipeline_smoke.py).
"""

from __future__ import annotations

import pytest

from salespulse.crm.registry import CRMRegistry


def test_registry_lists_all_four_adapters():
    adapters = CRMRegistry.available()
    assert set(adapters) == {"hubspot", "salesforce", "pipedrive", "webhook"}


def test_registry_get_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        CRMRegistry.get("hubspot", api_key="test", portal_id="123")


def test_asr_registry_lists_all_three_providers():
    from salespulse.asr.registry import ASRRegistry

    providers = ASRRegistry.available()
    assert set(providers) == {"whisper_local", "deepgram", "assemblyai"}
