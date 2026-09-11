"""
scoring/evidence.py

Evidence verification — checks that LLM-provided quotes exist in the transcript.
Guards against hallucinated evidence.

Interface:
    verify_evidence(quote, transcript) -> EvidenceVerification
    resolve_timestamp(timestamp_str, transcript) -> float | None
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..transcript.models import Transcript, Turn


@dataclass
class EvidenceVerification:
    quote: str
    verified: bool
    match_score: float
    matched_turn: Turn | None
    resolved_seconds: float | None


def verify_evidence(
    quote: str,
    transcript: Transcript,
    min_match_score: float = 0.75,
) -> EvidenceVerification:
    """
    Check whether quote appears in the transcript using token overlap.
    Threshold lowered to 0.75 to handle minor transcription variants.
    """
    if not quote:
        return EvidenceVerification(
            quote=quote,
            verified=False,
            match_score=0.0,
            matched_turn=None,
            resolved_seconds=None,
        )

    quote_tokens = _tokenise(quote)
    best_score = 0.0
    best_turn: Turn | None = None

    for turn in transcript.turns:
        score = _token_overlap(quote_tokens, _tokenise(turn.text))
        if score > best_score:
            best_score = score
            best_turn = turn

    verified = best_score >= min_match_score
    resolved = best_turn.start if (verified and best_turn) else None

    return EvidenceVerification(
        quote=quote,
        verified=verified,
        match_score=round(best_score, 3),
        matched_turn=best_turn if verified else None,
        resolved_seconds=resolved,
    )


def resolve_timestamp(
    timestamp_str: str,
    transcript: Transcript,
) -> float | None:
    """
    Parse MM:SS or HH:MM:SS and return seconds from call start.
    Returns None if unparseable or out of range.
    """
    if not timestamp_str:
        return None
    parts = timestamp_str.strip().split(":")
    try:
        if len(parts) == 2:
            seconds = int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            return None
    except ValueError:
        return None

    if seconds > transcript.duration_seconds:
        return None
    return float(seconds)


def _tokenise(text: str) -> set[str]:
    """Lowercase, strip punctuation, split into token set."""
    return set(re.sub(r"[^\w\s]", "", text.lower()).split())


def _token_overlap(a: set[str], b: set[str]) -> float:
    """Jaccard-like: |intersection| / |union|."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
