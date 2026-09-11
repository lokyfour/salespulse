"""
pipeline/tasks.py

Celery task definitions.

Mock pipeline:
  - transcribe_audio  → returns fixture transcript (skips Whisper)
  - diarize_audio     → no-op (fixture already has speaker labels)
  - normalise_transcript → loads fixture via normaliser.normalise_from_fixture
  - score_transcript  → REAL LLM scoring via scoring engine
  - generate_coaching → stub (logs result)
  - push_to_crm       → stub (logs result)

To switch from mock to real ASR, set MOCK_ASR=false in .env and ensure
DEEPGRAM_API_KEY or HF_TOKEN is set.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from pathlib import Path

from celery.exceptions import MaxRetriesExceededError

from .celery_app import app
from .state import PipelineStage, advance, fail, get_stage, register

logger = logging.getLogger(__name__)

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures"
MOCK_ASR = os.environ.get("MOCK_ASR", "true").lower() == "true"


# ── In-memory call store for mock pipeline ────────────────────────────────────
# Production: replace with PostgreSQL reads via SQLAlchemy.
_call_store: dict[str, dict] = {}  # call_id → {audio_path, rep_id, ...}
_transcript_store: dict[str, object] = {}  # call_id → Transcript


def enqueue_call(
    audio_path: str,
    rep_id: str,
    crm_deal_id: str | None = None,
) -> str:
    """
    Register a call and dispatch the pipeline.
    Returns call_id string.
    """
    call_id = str(uuid.uuid4())
    _call_store[call_id] = {
        "audio_path": audio_path,
        "rep_id": rep_id,
        "crm_deal_id": crm_deal_id,
    }
    register(uuid.UUID(call_id))
    transcribe_audio.delay(call_id)
    return call_id


# ── Stage 1: ASR ──────────────────────────────────────────────────────────────


@app.task(
    bind=True,
    queue="asr",
    max_retries=3,
    default_retry_delay=30,
    name="salespulse.transcribe_audio",
)
def transcribe_audio(self, call_id: str) -> dict:
    """Stage 1: Transcribe audio. Uses fixture in mock mode."""
    try:
        advance(uuid.UUID(call_id), PipelineStage.TRANSCRIBING)

        if MOCK_ASR:
            logger.info("MOCK_ASR=true — using fixture transcript for call %s", call_id)
            # Store a marker; normalise_transcript will load the fixture
            _call_store.setdefault(call_id, {})["_mock_asr"] = True
        else:
            # Real path: load audio, run ASR provider
            from ..asr.base import ASRConfig
            from ..asr.registry import ASRRegistry

            meta = _call_store[call_id]
            provider = ASRRegistry.get(
                os.environ.get("ASR_PROVIDER", "whisper_local"),
                api_key=os.environ.get("DEEPGRAM_API_KEY"),
            )
            config = ASRConfig(language=None, model="large-v3")
            raw = provider.transcribe(Path(meta["audio_path"]), config)
            _call_store[call_id]["_raw_transcript"] = raw

        diarize_audio.delay(call_id)
        return {"call_id": call_id, "status": "transcribed"}

    except Exception as exc:
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            fail(uuid.UUID(call_id), PipelineStage.TRANSCRIBING, str(exc))
            raise


# ── Stage 2: Diarization ──────────────────────────────────────────────────────


@app.task(
    bind=True,
    queue="diarize",
    max_retries=3,
    default_retry_delay=30,
    name="salespulse.diarize_audio",
)
def diarize_audio(self, call_id: str) -> dict:
    """Stage 2: Speaker diarization. No-op in mock mode (fixture has labels)."""
    try:
        advance(uuid.UUID(call_id), PipelineStage.DIARIZING)

        if not MOCK_ASR:
            # Real path: run pyannote diarization
            from ..diarization.aligner import align
            from ..diarization.diarizer import DiarizationConfig, Diarizer
            from ..diarization.speaker_map import SpeakerMapConfig, resolve_speakers

            meta = _call_store[call_id]
            raw = meta["_raw_transcript"]
            diarizer = Diarizer(hf_token=os.environ.get("HF_TOKEN"))
            segments = diarizer.diarize(
                Path(meta["audio_path"]),
                DiarizationConfig(min_speakers=2, max_speakers=4),
            )
            attributed = align(raw.words, segments)
            speaker_map = resolve_speakers(
                segments,
                SpeakerMapConfig(explicit_map={"SPEAKER_00": "rep", "SPEAKER_01": "prospect"}),
            )
            _call_store[call_id]["_attributed_words"] = attributed
            _call_store[call_id]["_speaker_map"] = speaker_map

        normalise_transcript.delay(call_id)
        return {"call_id": call_id, "status": "diarized"}

    except Exception as exc:
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            fail(uuid.UUID(call_id), PipelineStage.DIARIZING, str(exc))
            raise


# ── Stage 3: Normalise ────────────────────────────────────────────────────────


@app.task(
    bind=True,
    queue="score",
    max_retries=3,
    default_retry_delay=30,
    name="salespulse.normalise_transcript",
)
def normalise_transcript(self, call_id: str) -> dict:
    """Stage 3: Build canonical Transcript."""
    try:
        advance(uuid.UUID(call_id), PipelineStage.NORMALISING)

        if MOCK_ASR:
            from ..transcript.normaliser import normalise_from_fixture

            fixture = FIXTURE_DIR / "sample_transcript.json"
            transcript = normalise_from_fixture(fixture, uuid.UUID(call_id))
        else:
            from ..transcript.normaliser import NormaliserConfig, normalise

            meta = _call_store[call_id]
            raw = meta["_raw_transcript"]
            transcript = normalise(
                words=meta["_attributed_words"],
                speaker_map=meta["_speaker_map"],
                config=NormaliserConfig(),
                call_id=uuid.UUID(call_id),
                language=raw.language,
                duration_seconds=raw.duration,
            )

        _transcript_store[call_id] = transcript
        score_transcript.delay(call_id)
        return {"call_id": call_id, "status": "normalised"}

    except Exception as exc:
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            fail(uuid.UUID(call_id), PipelineStage.NORMALISING, str(exc))
            raise


# ── Stage 4: Score ────────────────────────────────────────────────────────────


@app.task(
    bind=True,
    queue="score",
    max_retries=3,
    default_retry_delay=60,
    name="salespulse.score_transcript",
)
def score_transcript(self, call_id: str) -> dict:
    """
    Stage 4: Score the transcript against the rubric using a real LLM call.

    This is the only stage that calls an external API in the mock pipeline.
    Requires OPENAI_API_KEY (or ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic).
    """
    try:
        advance(uuid.UUID(call_id), PipelineStage.SCORING)

        transcript = _transcript_store[call_id]

        # Load rubric
        from ..scoring.rubric import load_rubric

        rubric_path = Path(os.environ.get("RUBRIC_PATH", "config/rubric.example.yaml"))
        rubric = load_rubric(rubric_path)

        # Compute rule-based metrics
        from ..scoring.metrics import MetricsConfig, compute_metrics

        competitor_list = os.environ.get(
            "COMPETITOR_LIST", "Gong,Chorus,Salesloft,Outreach,HubSpot,Salesforce"
        ).split(",")
        metrics = compute_metrics(transcript, MetricsConfig(competitor_names=competitor_list))

        # Build LLM prompt
        from ..scoring.prompt_builder import build_prompt

        system_prompt, user_prompt = build_prompt(transcript, rubric)

        # Call LLM
        from ..scoring.llm_scorer import LLMConfig, get_scorer

        llm_config = LLMConfig(
            provider=os.environ.get("LLM_PROVIDER", "openai"),
            model=os.environ.get("LLM_MODEL", "gpt-4o"),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.1")),
            api_key=os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"),
            base_url=os.environ.get("OLLAMA_BASE_URL"),
        )
        scorer = get_scorer(llm_config)
        raw_scorecard = scorer.score(system_prompt, user_prompt)

        # Override computed metrics into LLM response
        # (LLM does not re-compute talk_ratio — we inject the accurate value)
        if "conversation_metrics" not in raw_scorecard:
            raw_scorecard["conversation_metrics"] = {}
        raw_scorecard["conversation_metrics"]["talk_ratio"] = metrics.talk_ratio
        raw_scorecard["conversation_metrics"]["next_step_confirmed"] = metrics.next_step_confirmed
        raw_scorecard["conversation_metrics"]["competitor_mentions"] = metrics.competitor_mentions
        raw_scorecard["conversation_metrics"]["objections_handled"] = metrics.objections_raised

        # Build and validate Scorecard
        from ..scoring.scorecard import build_scorecard

        scorecard = build_scorecard(raw_scorecard, rubric, uuid.UUID(call_id), transcript)

        logger.info(
            "Scored call %s: overall=%d, flags=%d",
            call_id,
            scorecard.overall_score,
            len(scorecard.coaching_flags),
        )

        # Store in memory for downstream tasks
        _call_store[call_id]["_scorecard"] = scorecard

        generate_coaching.delay(call_id)
        return {
            "call_id": call_id,
            "status": "scored",
            "overall_score": scorecard.overall_score,
        }

    except Exception as exc:
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            fail(uuid.UUID(call_id), PipelineStage.SCORING, str(exc))
            raise


# ── Stage 5: Coaching ─────────────────────────────────────────────────────────


@app.task(
    bind=True,
    queue="coaching",
    max_retries=2,
    default_retry_delay=10,
    name="salespulse.generate_coaching",
)
def generate_coaching(self, call_id: str) -> dict:
    """Stage 5: Log coaching flags. Full implementation writes to DB."""
    try:
        advance(uuid.UUID(call_id), PipelineStage.COACHING)
        scorecard = _call_store[call_id].get("_scorecard")
        if scorecard:
            for flag in scorecard.coaching_flags:
                logger.info("COACHING [%s]: %s", call_id[:8], flag)

        push_to_crm.delay(call_id)
        return {"call_id": call_id, "status": "coaching_updated"}

    except Exception as exc:
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            fail(uuid.UUID(call_id), PipelineStage.COACHING, str(exc))
            raise


# ── Stage 6: CRM push ─────────────────────────────────────────────────────────


@app.task(
    bind=True,
    queue="crm_push",
    max_retries=5,
    default_retry_delay=30,
    name="salespulse.push_to_crm",
)
def push_to_crm(self, call_id: str) -> dict:
    """Stage 6: Push scorecard to CRM. Logs result in mock mode."""
    try:
        advance(uuid.UUID(call_id), PipelineStage.SYNCING_CRM)
        scorecard = _call_store[call_id].get("_scorecard")
        crm_adapter = os.environ.get("CRM_ADAPTER", "")

        if crm_adapter and scorecard:
            from ..crm.registry import CRMRegistry

            try:
                adapter = CRMRegistry.get(crm_adapter)
                crm_deal_id = _call_store[call_id].get("crm_deal_id")
                result = asyncio.run(
                    adapter.push_scorecard(uuid.UUID(call_id), scorecard, crm_deal_id)
                )
                logger.info(
                    "CRM push for call %s: success=%s record_id=%s",
                    call_id,
                    result.success,
                    result.crm_record_id,
                )
            except NotImplementedError:
                logger.info(
                    "CRM adapter '%s' not implemented yet — scorecard for call %s "
                    "logged only (score %d)",
                    crm_adapter,
                    call_id,
                    scorecard.overall_score,
                )
        else:
            logger.info("CRM_ADAPTER not set — scorecard for call %s logged only", call_id)

        advance(uuid.UUID(call_id), PipelineStage.COMPLETE)
        return {"call_id": call_id, "status": "complete"}

    except Exception as exc:
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            fail(uuid.UUID(call_id), PipelineStage.SYNCING_CRM, str(exc))
            raise


# ── Public helpers ────────────────────────────────────────────────────────────


def get_call_result(call_id: str) -> dict:
    """
    Return the current state and scorecard for a call.
    Used by the API status endpoint.
    """
    from .state import get_error

    try:
        stage = get_stage(uuid.UUID(call_id))
    except KeyError:
        return {"error": "call_not_found"}

    result: dict = {"call_id": call_id, "stage": stage.value}

    scorecard = _call_store.get(call_id, {}).get("_scorecard")
    if scorecard:
        result["overall_score"] = scorecard.overall_score
        result["coaching_flags"] = scorecard.coaching_flags
        result["criteria_scores"] = [
            {
                "criterion_id": cs.criterion_id,
                "label": cs.label,
                "score": cs.score,
                "weight": cs.weight,
                "evidence": cs.evidence,
                "timestamp": cs.timestamp,
                "flag": cs.flag,
            }
            for cs in scorecard.criteria_scores
        ]
        result["conversation_metrics"] = {
            "talk_ratio": scorecard.conversation_metrics.talk_ratio,
            "next_step_confirmed": scorecard.conversation_metrics.next_step_confirmed,
            "objections_handled": scorecard.conversation_metrics.objections_handled,
            "competitor_mentions": scorecard.conversation_metrics.competitor_mentions,
        }
        result["overall_notes"] = scorecard.overall_notes

    error = get_error(uuid.UUID(call_id))
    if error:
        result["error"] = error

    return result
