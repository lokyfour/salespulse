"""
tests/test_llm_scorer.py

Unit tests for scoring/llm_scorer.py. No network calls — only JSON
parsing and backend selection are exercised.
"""

from __future__ import annotations

import pytest

from salespulse.scoring.llm_scorer import (
    AnthropicScorerBackend,
    LLMConfig,
    OllamaScorerBackend,
    OpenAIScorerBackend,
    ScoringError,
    _parse_json,
    get_scorer,
)


def test_parse_json_clean_string():
    result = _parse_json('{"a": 1, "b": "two"}')
    assert result == {"a": 1, "b": "two"}


def test_parse_json_strips_markdown_fences():
    raw = '```json\n{"a": 1}\n```'
    assert _parse_json(raw) == {"a": 1}


def test_parse_json_invalid_raises_scoring_error():
    with pytest.raises(ScoringError):
        _parse_json("not json at all")


def test_get_scorer_openai_returns_openai_backend():
    config = LLMConfig(provider="openai", model="gpt-4o")
    scorer = get_scorer(config)
    assert isinstance(scorer, OpenAIScorerBackend)


def test_get_scorer_anthropic_returns_anthropic_backend():
    config = LLMConfig(provider="anthropic", model="claude-3")
    scorer = get_scorer(config)
    assert isinstance(scorer, AnthropicScorerBackend)


def test_get_scorer_ollama_returns_ollama_backend():
    config = LLMConfig(provider="ollama", model="llama3")
    scorer = get_scorer(config)
    assert isinstance(scorer, OllamaScorerBackend)


def test_get_scorer_unknown_provider_raises():
    config = LLMConfig(provider="not-a-real-provider", model="x")
    with pytest.raises(ValueError):
        get_scorer(config)
