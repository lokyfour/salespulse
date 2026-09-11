"""
scoring/llm_scorer.py

LLM scoring backends. Returns parsed JSON scorecard dict.

Interface:
    get_scorer(config) -> LLMScorer
    scorer.score(system_prompt, user_prompt) -> dict
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMConfig:
    provider: str       # "openai" | "anthropic" | "ollama"
    model: str
    temperature: float = 0.1
    max_tokens: int = 2048
    api_key: str | None = None
    base_url: str | None = None


class LLMScorer(ABC):
    @abstractmethod
    def score(self, system_prompt: str, user_prompt: str) -> dict:
        raise NotImplementedError


class OpenAIScorerBackend(LLMScorer):
    """OpenAI Chat Completions with JSON mode."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config

    def score(self, system_prompt: str, user_prompt: str) -> dict:
        from openai import OpenAI

        client = OpenAI(
            api_key=self._config.api_key,
            base_url=self._config.base_url,
        )
        response = client.chat.completions.create(
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content or ""
        return _parse_json(raw)


class AnthropicScorerBackend(LLMScorer):
    """Anthropic Messages API backend."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config

    def score(self, system_prompt: str, user_prompt: str) -> dict:
        import anthropic

        client = anthropic.Anthropic(api_key=self._config.api_key)
        message = client.messages.create(
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = message.content[0].text
        return _parse_json(raw)


class OllamaScorerBackend(LLMScorer):
    """Ollama local API (OpenAI-compatible endpoint)."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config

    def score(self, system_prompt: str, user_prompt: str) -> dict:
        from openai import OpenAI

        client = OpenAI(
            api_key="ollama",
            base_url=self._config.base_url or "http://localhost:11434/v1",
        )
        response = client.chat.completions.create(
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content or ""
        return _parse_json(raw)


def get_scorer(config: LLMConfig) -> LLMScorer:
    """Return the appropriate backend for the given config."""
    backends = {
        "openai": OpenAIScorerBackend,
        "anthropic": AnthropicScorerBackend,
        "ollama": OllamaScorerBackend,
    }
    if config.provider not in backends:
        raise ValueError(
            f"Unknown LLM provider '{config.provider}'. "
            f"Choose from: {list(backends)}"
        )
    return backends[config.provider](config)


def _parse_json(raw: str) -> dict:
    """Parse LLM response to dict. Strip markdown fences if present."""
    text = raw.strip()
    # Strip ```json ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ScoringError(f"LLM returned invalid JSON: {e}\nRaw: {raw[:300]}") from e


class ScoringError(Exception):
    pass
