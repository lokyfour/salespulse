"""
scoring/metrics.py

Rule-based conversation metrics computed directly from the Transcript.
These are deterministic — no LLM call needed.

Interface:
    compute_metrics(transcript, config) -> ComputedMetrics
    detect_competitors(transcript, competitor_names) -> list[str]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..transcript.models import Transcript


@dataclass
class MetricsConfig:
    competitor_names: list[str] = field(default_factory=list)
    next_step_phrases: list[str] = field(default_factory=lambda: [
        "follow up", "send over", "schedule", "tuesday", "monday", "friday",
        "thursday", "wednesday", "next week", "i'll send", "let's connect",
        "book a call", "calendar invite", "i will send", "set up a call",
    ])


@dataclass
class ComputedMetrics:
    talk_ratio: float
    next_step_confirmed: bool
    competitor_mentions: list[str]
    # Count of objection phrases spoken by the prospect. NOT the same as
    # objections the rep successfully handled — handling detection is not
    # implemented; downstream consumers must not treat this as "resolved".
    objections_raised: int
    call_duration_seconds: float


_OBJECTION_PATTERNS = re.compile(
    r"\b(too expensive|not in the budget|already have|using \w+|"
    r"not the right time|need to think|not sure|concerns? about|"
    r"what about the price|pricing is|cost is)\b",
    re.IGNORECASE,
)


def compute_metrics(
    transcript: Transcript,
    config: MetricsConfig,
) -> ComputedMetrics:
    """
    Compute rule-based metrics from a normalised Transcript.
    """
    rep_time = sum(t.duration for t in transcript.rep_turns)
    total_time = transcript.duration_seconds
    talk_ratio = round(rep_time / total_time, 3) if total_time > 0 else 0.0

    # Next step: check the last 3 rep turns for scheduling language
    last_rep_turns = transcript.rep_turns[-3:] if transcript.rep_turns else []
    last_rep_text = " ".join(t.text.lower() for t in last_rep_turns)
    next_step = any(phrase in last_rep_text for phrase in config.next_step_phrases)

    competitors = detect_competitors(transcript, config.competitor_names)

    # Count objections raised across all prospect turns (not whether handled)
    prospect_text = " ".join(t.text for t in transcript.prospect_turns)
    objections_raised = len(_OBJECTION_PATTERNS.findall(prospect_text))

    return ComputedMetrics(
        talk_ratio=talk_ratio,
        next_step_confirmed=next_step,
        competitor_mentions=competitors,
        objections_raised=objections_raised,
        call_duration_seconds=transcript.duration_seconds,
    )


def detect_competitors(
    transcript: Transcript,
    competitor_names: list[str],
) -> list[str]:
    """
    Return the subset of competitor_names mentioned anywhere in the transcript.
    Case-insensitive whole-word match.
    """
    full_text = " ".join(t.text for t in transcript.turns)
    found = []
    for name in competitor_names:
        pattern = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
        if pattern.search(full_text):
            found.append(name)
    return found
