"""
scoring/scorecard.py

Scorecard domain model and build_scorecard factory.

Interface:
    build_scorecard(raw_dict, rubric, call_id) -> Scorecard
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ..transcript.models import Transcript
from .evidence import verify_evidence
from .rubric import RubricConfig


@dataclass
class CriterionScore:
    criterion_id: str
    label: str
    score: int
    weight: int
    evidence: str | None
    timestamp: str | None
    flag: str | None


@dataclass
class ConversationMetrics:
    talk_ratio: float
    next_step_confirmed: bool
    # Raw count of objections the prospect raised during the call. Despite the
    # field name, this does NOT indicate whether the rep successfully
    # addressed them — handling detection is not implemented upstream.
    objections_handled: int
    competitor_mentions: list[str] = field(default_factory=list)
    talk_ratio_flag: str | None = None


@dataclass
class Scorecard:
    call_id: UUID
    rubric_name: str
    rubric_version: str
    criteria_scores: list[CriterionScore]
    conversation_metrics: ConversationMetrics
    overall_notes: str

    @property
    def overall_score(self) -> int:
        """Weighted sum normalised to 0–100."""
        total = sum((cs.score / 3.0) * cs.weight for cs in self.criteria_scores)
        return round(total)

    @property
    def coaching_flags(self) -> list[str]:
        flags = []
        for cs in self.criteria_scores:
            if cs.score == 0 and cs.flag:
                flags.append(f"{cs.label} not identified — {cs.flag}")
            elif cs.score == 1:
                flags.append(f"{cs.label} score 1/3 — needs development")
        m = self.conversation_metrics
        if m.talk_ratio_flag == "too_high":
            flags.append(
                f"Rep talk ratio {m.talk_ratio:.0%} — above 55% threshold; ask more open questions"
            )
        elif m.talk_ratio_flag == "too_low":
            flags.append(
                f"Rep talk ratio {m.talk_ratio:.0%} — below 20%; consider more active guidance"
            )
        if not m.next_step_confirmed:
            flags.append("No next step confirmed — call ended without a specific follow-up")
        return flags


def build_scorecard(
    raw_dict: dict,
    rubric: RubricConfig,
    call_id: UUID,
    transcript: Transcript | None = None,
) -> Scorecard:
    """
    Build and validate a Scorecard from the raw LLM response dict.

    Args:
        raw_dict: Parsed JSON from the LLM scorer.
        rubric: Active rubric used for this call.
        call_id: UUID of the call being scored.
        transcript: If provided, evidence quotes are verified against it.

    Returns:
        Validated Scorecard.
    """
    {c.id for c in rubric.criteria}

    criteria_scores: list[CriterionScore] = []
    for raw_cs in raw_dict.get("criteria_scores", []):
        cid = raw_cs.get("criterion_id", "")
        criterion = rubric.criterion_by_id(cid)
        if criterion is None:
            continue  # skip unknown criteria

        raw_score = raw_cs.get("score") or 0
        score = int(raw_score)
        score = max(0, min(3, score))  # clamp to [0, 3]
        evidence = raw_cs.get("evidence") or None
        timestamp = raw_cs.get("timestamp") or None
        flag = raw_cs.get("flag") or None

        # Enforce evidence_required: zero score if no evidence provided
        if criterion.evidence_required and score > 0 and not evidence:
            score = 0
            flag = "evidence_missing"

        # Optionally verify evidence against transcript
        if transcript and evidence and score > 0:
            verification = verify_evidence(evidence, transcript)
            if not verification.verified:
                flag = f"evidence_unverified (match={verification.match_score:.2f})"
                if criterion.evidence_required:
                    score = 0

        criteria_scores.append(
            CriterionScore(
                criterion_id=cid,
                label=criterion.label,
                score=score,
                weight=criterion.weight,
                evidence=evidence,
                timestamp=timestamp,
                flag=flag,
            )
        )

    # Ensure every rubric criterion has a score entry (fill missing with 0)
    scored_ids = {cs.criterion_id for cs in criteria_scores}
    for criterion in rubric.criteria:
        if criterion.id not in scored_ids:
            criteria_scores.append(
                CriterionScore(
                    criterion_id=criterion.id,
                    label=criterion.label,
                    score=0,
                    weight=criterion.weight,
                    evidence=None,
                    timestamp=None,
                    flag="not_scored_by_llm",
                )
            )

    # Conversation metrics
    raw_m = raw_dict.get("conversation_metrics", {})
    talk_ratio = float(raw_m.get("talk_ratio", 0.0))
    talk_ratio = max(0.0, min(1.0, talk_ratio))

    talk_flag = None
    if talk_ratio > 0.55:
        talk_flag = "too_high"
    elif talk_ratio < 0.20:
        talk_flag = "too_low"

    conv_metrics = ConversationMetrics(
        talk_ratio=round(talk_ratio, 3),
        next_step_confirmed=bool(raw_m.get("next_step_confirmed", False)),
        objections_handled=int(raw_m.get("objections_handled", 0)),
        competitor_mentions=list(raw_m.get("competitor_mentions", [])),
        talk_ratio_flag=talk_flag,
    )

    return Scorecard(
        call_id=call_id,
        rubric_name=rubric.name,
        rubric_version=rubric.version,
        criteria_scores=criteria_scores,
        conversation_metrics=conv_metrics,
        overall_notes=str(raw_dict.get("overall_notes", "")),
    )
