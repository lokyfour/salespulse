"""
scoring/prompt_builder.py

Builds the LLM prompt from a Transcript and a RubricConfig.

Interface:
    build_prompt(transcript, rubric) -> tuple[str, str]  # system, user
"""

from __future__ import annotations

from ..transcript.models import Transcript
from .rubric import RubricConfig

_SYSTEM = """\
You are an expert sales quality evaluator. Your job is to score a sales call \
transcript against a provided rubric.

Rules:
- Score each criterion 0-3 using the scoring guide provided.
- For every score > 0 where evidence_required is true, you MUST provide a \
verbatim quote from the transcript and its timestamp.
- If you cannot find evidence for an evidence_required criterion, score it 0.
- Do not hallucinate quotes. Only use text that appears in the transcript.
- Compute talk_ratio as the fraction of [MM:SS] timestamps that belong to REP turns.
- Return ONLY valid JSON. No markdown, no explanation outside the JSON object.\
"""

_RESPONSE_FORMAT = """\

## Required JSON output format

{
  "criteria_scores": [
    {
      "criterion_id": "<id>",
      "score": <0-3>,
      "evidence": "<verbatim quote from transcript, or null>",
      "timestamp": "<MM:SS from transcript, or null>",
      "flag": "<reason if score=0 and evidence_required, else null>"
    }
  ],
  "conversation_metrics": {
    "talk_ratio": <float 0.0-1.0>,
    "next_step_confirmed": <true|false>,
    "objections_handled": <integer>,
    "competitor_mentions": [<string>, ...]
  },
  "overall_notes": "<2-3 sentence coaching summary>"
}\
"""


def build_prompt(
    transcript: Transcript,
    rubric: RubricConfig,
) -> tuple[str, str]:
    """
    Build the system and user prompt for the scoring LLM call.

    Returns:
        (system_prompt, user_prompt)
    """
    user = (
        f"## Transcript\n\n{transcript.as_prompt_string()}\n\n"
        f"## Rubric: {rubric.name} (v{rubric.version})\n\n"
        f"{_format_criteria_instructions(rubric)}"
        f"{_RESPONSE_FORMAT}"
    )
    return _SYSTEM, user


def _format_criteria_instructions(rubric: RubricConfig) -> str:
    lines = ["Score each criterion 0–3:\n"]
    for i, c in enumerate(rubric.criteria, 1):
        ev = " [EVIDENCE REQUIRED]" if c.evidence_required else ""
        lines.append(f"{i}. {c.label} (weight: {c.weight}%){ev}")
        lines.append(f"   {c.description}")
        lines.append(f"   0={c.scoring_guide.level_0}")
        lines.append(f"   1={c.scoring_guide.level_1}")
        lines.append(f"   2={c.scoring_guide.level_2}")
        lines.append(f"   3={c.scoring_guide.level_3}")
        lines.append("")
    return "\n".join(lines)
