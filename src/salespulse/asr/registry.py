"""
asr/registry.py

Provider registry — resolves a config string to an ASRProvider instance.

Usage:
    provider = ASRRegistry.get("deepgram", api_key=os.environ["DEEPGRAM_API_KEY"])
    transcript = provider.transcribe(path, config)

Registered providers:
    "whisper_local"  → WhisperLocalProvider
    "deepgram"       → DeepgramProvider
    "assemblyai"     → AssemblyAIProvider
"""

from __future__ import annotations

from typing import Any

from .assemblyai_provider import AssemblyAIProvider
from .base import ASRProvider
from .deepgram_provider import DeepgramProvider
from .whisper_provider import WhisperLocalProvider

_REGISTRY: dict[str, type[ASRProvider]] = {
    "whisper_local": WhisperLocalProvider,
    "deepgram": DeepgramProvider,
    "assemblyai": AssemblyAIProvider,
}


class ASRRegistry:
    """Factory for ASR providers. Keyed by the `asr.provider` config value."""

    @staticmethod
    def get(provider_name: str, **kwargs: Any) -> ASRProvider:
        """
        Return an instantiated ASR provider.

        Args:
            provider_name: Registry key (e.g. "deepgram").
            **kwargs: Constructor arguments forwarded to the provider class.

        Returns:
            Concrete ASRProvider instance.

        Raises:
            KeyError: If `provider_name` is not registered.
        """
        raise NotImplementedError

    @staticmethod
    def available() -> list[str]:
        """Return the list of registered provider names."""
        return list(_REGISTRY.keys())
