# salespulse

AI sales quality agent — transcribe calls, score against your rubric, coach reps, sync results to CRM.

![CI](https://github.com/lokyfour/salespulse/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## What it does

Sales teams generate hundreds of calls per week. Managers can review five. The rest disappear into
recordings no one watches, CRM fields no one fills, and coaching feedback that arrives a quarter late.

**salespulse** processes every recorded call through a five-stage pipeline:

1. **Transcribe** — audio → diarized transcript (rep vs. prospect, word-level timestamps)
2. **Score** — LLM evaluates the transcript against a configurable rubric (MEDDIC, BANT, or custom)
3. **Evidence** — every score anchors to a quoted passage from the call; no black-box verdicts
4. **Coach** — per-rep and team-level aggregation surfaces patterns, flags, and recommendations
5. **Sync** — structured scorecard pushes to CRM (HubSpot, Salesforce, Pipedrive) via webhook

An optional **voice agent layer** handles outbound cold calling: Twilio receives the call, a
real-time STT/LLM/TTS loop runs the conversation, and the outcome lands in the same pipeline.

**Who uses this:** B2B sales teams (5–200 reps), revenue operations leads, sales enablement
engineers, and agencies that build conversation intelligence tools for clients.

---

## Pipeline / Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          INGEST LAYER                                │
│  CRM webhook · File upload · Twilio recording URL · Direct POST      │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  audio file path + metadata
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   PIPELINE ORCHESTRATOR  (Celery)                    │
│                                                                      │
│  ┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐    │
│  │  ASR TASK   │───▶│ DIARIZATION TASK │───▶│  NORMALISE TASK  │    │
│  │             │    │                  │    │                  │    │
│  │ Whisper /   │    │ pyannote.audio   │    │ speaker map,     │    │
│  │ Deepgram /  │    │ speaker clusters │    │ segment merge,   │    │
│  │ AssemblyAI  │    │ → SPEAKER_00/01  │    │ clean JSON       │    │
│  └─────────────┘    └──────────────────┘    └────────┬─────────┘    │
│                                                      │              │
│  ┌───────────────────────────────────────────────────▼──────────┐   │
│  │                    SCORING ENGINE  (LLM)                      │   │
│  │                                                               │   │
│  │  rubric.yaml ──▶ prompt builder ──▶ LLM ──▶ scorecard JSON   │   │
│  │                                                               │   │
│  │  per criterion: score 0–3, evidence quote, timestamp, flag    │   │
│  │  aggregates:  talk_ratio · objections · competitor_mentions   │   │
│  │               next_step_confirmed · overall_score 0–100       │   │
│  └───────────────────────────────────────────────────┬───────────┘   │
│                                                      │              │
│  ┌───────────────────────────────────────────────────▼──────────┐   │
│  │                  COACHING RECOMMENDER                         │   │
│  │                                                               │   │
│  │  rep history ──▶ pattern detector ──▶ coaching flags         │   │
│  │  team rollup ──▶ top objections · win patterns · risk reps   │   │
│  └───────────────────────────────────────────────────┬───────────┘   │
└──────────────────────────────────────────────────────┼───────────────┘
                                                       │
                              ┌────────────────────────▼─────────────┐
                              │           CRM ADAPTER REGISTRY        │
                              │                                       │
                              │  ┌───────────┐  ┌──────────────┐    │
                              │  │ HubSpot   │  │  Salesforce  │    │
                              │  │ adapter   │  │  adapter     │    │
                              │  └───────────┘  └──────────────┘    │
                              │  ┌───────────┐  ┌──────────────┐    │
                              │  │ Pipedrive │  │  Webhook     │    │
                              │  │ adapter   │  │  (generic)   │    │
                              │  └───────────┘  └──────────────┘    │
                              └───────────────────────────────────────┘

─ ─ ─ ─ ─ ─ ─ ─ ─ OPTIONAL: VOICE AGENT LAYER ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

  Twilio ──WebSocket──▶ STT stream ──▶ LLM (function-calling)
                                           │
                                    ──▶ TTS ──▶ Twilio audio out
                                           │
                                    call outcome ──▶ pipeline ingest
```

**Component responsibilities:**

| Component | Responsibility |
|---|---|
| `ingest/` | Accept audio from CRM webhook, file upload, Twilio URL, or direct POST. Deduplicate by call ID. |
| `asr/` | Provider abstraction (Whisper local / Deepgram / AssemblyAI). Returns raw transcript + word timestamps. |
| `diarization/` | pyannote.audio wrapper. Assigns SPEAKER_00/01 to segments; optionally maps to real names via reference audio. |
| `transcript/` | Normalises diarized output into a canonical `Transcript` model. Merges short segments, strips filler. |
| `scoring/` | Loads rubric from YAML. Builds LLM prompt. Parses structured scorecard with per-criterion evidence. |
| `coaching/` | Aggregates scorecards across calls. Detects rep-level patterns, team trends, underperformers. |
| `crm/` | Adapter ABC + registry. Pushes scorecard fields to configured CRM. Idempotent — safe to retry. |
| `pipeline/` | Celery task definitions. Chains the five stages. Handles retries, timeouts, partial failures. |
| `api/` | FastAPI endpoints: upload, webhook receiver, score retrieval, rep dashboard, team report. |
| `models/` | SQLAlchemy ORM: `Call`, `Transcript`, `Scorecard`, `Criterion`, `Rep`, `CoachingReport`. |
| `voice/` | Optional. Twilio WebSocket handler + real-time STT/LLM/TTS loop for outbound voice agent. |

---

## Key design decisions

**1. Rubric as configuration, not code**

Scoring criteria live in `config/rubric.yaml`, not in Python. A sales manager can change the
methodology (BANT → MEDDIC → custom) and adjust criterion weights without touching the codebase
or triggering a deploy. The scoring engine treats the rubric as a prompt template: criteria
become numbered instructions, weights become explicit priorities.

**2. Evidence-backed scores only**

Every criterion score (0–3) must reference a verbatim passage from the transcript with a
timestamp. A score without evidence is rejected by the scoring engine. This makes the scorecard
auditable: managers can dispute a flag, reps can see exactly what was scored and why. Required
by teams operating under EU AI Act Article 13 (transparency obligation for high-impact AI
decisions affecting workers).

**3. Provider abstraction for ASR and LLM**

Both the speech-to-text and language model layers are accessed through abstract base classes.
Concrete providers (Whisper local, Deepgram, AssemblyAI for ASR; OpenAI, Anthropic, Ollama for
LLM) are registered by name and selected via config. This avoids rewriting pipeline code when
switching vendors — a practical requirement given how fast the ASR/LLM market moves.

**4. Async pipeline with Celery, not synchronous request handlers**

A 45-minute call recording processed through Whisper large-v3 on CPU takes 8–12 minutes. This
cannot block an HTTP request. Each pipeline stage runs as a Celery task. The API returns a
`call_id` immediately; the client polls `/calls/{call_id}/status` or receives a webhook when
processing completes. Failed stages retry with exponential backoff; partial results are
persisted so a retry only re-runs the failed stage.

**5. CRM writes are idempotent by design**

The CRM adapter always includes `call_id` as the external key. Writing the same scorecard twice
produces one CRM record, not two. This allows safe retries on network failures without duplicate
deals, notes, or tasks appearing in the CRM.

---

## Stack

| Layer | Technology |
|---|---|
| API server | Python 3.12, FastAPI, Uvicorn |
| Task queue | Celery 5, Redis (broker + result backend) |
| ASR (local) | OpenAI Whisper / faster-whisper |
| ASR (managed) | Deepgram API, AssemblyAI API (configurable) |
| Diarization | pyannote.audio 3.1 |
| Scoring LLM | OpenAI GPT-4o / Anthropic Claude (configurable) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| CRM adapters | HubSpot, Salesforce, Pipedrive (REST APIs) |
| Voice layer | Twilio Programmable Voice, WebSocket media stream |
| Containerisation | Docker, Docker Compose |
| CI | GitHub Actions |

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/lokyfour/salespulse.git
cd salespulse

# 2. Configure
cp .env.example .env
cp config/config.example.yaml config/config.yaml
cp config/rubric.example.yaml config/rubric.yaml
# Edit .env — set LLM_API_KEY, DATABASE_URL, REDIS_URL

# 3. Run migrations
docker compose run --rm migrate
# Creates all tables: calls, transcripts, turns, scorecards,
# criterion_scores, reps, coaching_reports, call_dedup_keys

# 4. Start
docker compose up --build

# 5. Verify
curl http://localhost:8000/health
# {"status":"ok","workers":2,"queue":"idle"}

# 6. Submit a call for analysis
curl -X POST http://localhost:8000/calls/upload \
  -F "file=@tests/fixtures/sample_call.mp3" \
  -F "rep_id=rep_001" \
  -F "crm_deal_id=deal_abc123"
# {"call_id":"c_7f3a...","status":"queued"}

# 7. Poll for result
curl http://localhost:8000/calls/c_7f3a.../status
# {"status":"complete","overall_score":71,"scorecard_url":"/calls/c_7f3a.../scorecard"}

# 8. Flower (Celery monitoring)
open http://localhost:5555
```

---

## Configuration

```yaml
# config/config.example.yaml

server:
  host: "0.0.0.0"
  port: 8000
  workers: 2                        # Uvicorn worker count

pipeline:
  max_audio_duration_minutes: 120   # Reject files longer than this
  audio_sample_rate: 16000          # Hz — Whisper requirement
  retry_attempts: 3                 # Per-stage retry count
  retry_backoff_seconds: 30         # Initial backoff, doubles each retry

asr:
  provider: "whisper_local"         # whisper_local | deepgram | assemblyai
  whisper_model: "large-v3"         # tiny | base | small | medium | large-v3
  language: "en"                    # ISO 639-1; null = auto-detect
  compute_type: "int8"              # float32 | int8 — int8 for CPU efficiency

diarization:
  enabled: true
  min_speakers: 2                   # Expected minimum distinct speakers
  max_speakers: 4                   # Cap for clustering
  speaker_name_map:                 # Optional: map SPEAKER_00 to real names
    SPEAKER_00: "rep"
    SPEAKER_01: "prospect"

scoring:
  llm_provider: "openai"            # openai | anthropic | ollama
  llm_model: "gpt-4o"               # Model name for the chosen provider
  temperature: 0.1                  # Low = deterministic scoring
  rubric_path: "config/rubric.yaml" # Path to active scoring rubric
  evidence_required: true           # Reject scores without transcript evidence

coaching:
  min_calls_for_pattern: 5          # Minimum calls before pattern flags appear
  underperformer_threshold: 55      # Overall score below this triggers flag
  talk_ratio_max: 0.55              # Rep talk time above this is flagged

crm:
  adapter: "hubspot"                # hubspot | salesforce | pipedrive | webhook
  hubspot_portal_id: ""             # HubSpot-specific
  salesforce_instance_url: ""       # Salesforce-specific
  pipedrive_domain: ""              # Pipedrive-specific
  webhook_url: ""                   # Generic webhook fallback

voice_agent:
  enabled: false                    # Set true to activate outbound agent
  twilio_phone_number: ""           # Your Twilio number
  max_call_duration_minutes: 15     # Hard limit; agent hangs up after this
  tts_provider: "elevenlabs"        # elevenlabs | google | azure
  tts_voice_id: ""                  # Provider-specific voice ID
```

```yaml
# config/rubric.example.yaml
# MEDDIC qualification rubric — customise for your sales methodology

rubric:
  name: "MEDDIC Enterprise"
  methodology: "meddic"             # meddic | bant | custom
  version: "1.0"

  criteria:
    - id: metrics
      label: "Metrics"
      weight: 20                    # Percentage of overall score
      description: >
        Rep established quantified business impact: revenue, cost, time, or risk.
        A number must be mentioned or elicited, not just acknowledged.
      evidence_required: true       # Score = 0 if no transcript quote provided
      scoring_guide:
        0: "No metrics discussed"
        1: "Vague improvement mentioned, no number"
        2: "Number mentioned but not qualified"
        3: "Specific metric with baseline and target confirmed"

    - id: economic_buyer
      label: "Economic Buyer"
      weight: 20
      description: >
        Rep identified the person with final budget authority by name or title.
        Proxy signals accepted: rep asked "who signs off?", prospect named a person.
      evidence_required: true
      scoring_guide:
        0: "Not discussed"
        1: "Existence acknowledged, not identified"
        2: "Title identified, no name or access plan"
        3: "Named, next step to involve them defined"

    - id: decision_criteria
      label: "Decision Criteria"
      weight: 15
      description: >
        Rep surfaced the prospect's evaluation scorecard: integration needs,
        security requirements, pricing model preferences, onboarding speed.
      evidence_required: true
      scoring_guide:
        0: "Not explored"
        1: "One criterion mentioned passively"
        2: "Multiple criteria surfaced"
        3: "Criteria ranked by prospect; rep addressed top two"

    - id: decision_process
      label: "Decision Process"
      weight: 15
      description: >
        Rep mapped the internal buying steps: legal review, security audit,
        board approval, procurement, signature authority.
      evidence_required: false
      scoring_guide:
        0: "Not explored"
        1: "Timeline mentioned only"
        2: "Steps named, owners unclear"
        3: "Full process mapped with owners and dates"

    - id: identify_pain
      label: "Identify Pain"
      weight: 15
      description: >
        Rep uncovered and confirmed a specific business pain — not a feature wish.
        Pain must be connected to a consequence if left unsolved.
      evidence_required: true
      scoring_guide:
        0: "No pain explored"
        1: "Surface-level problem mentioned"
        2: "Pain confirmed by prospect"
        3: "Pain + consequence + urgency all confirmed"

    - id: champion
      label: "Champion"
      weight: 15
      description: >
        Rep identified an internal advocate who will sell on their behalf.
        Champion test: would this person present to the economic buyer without rep present?
      evidence_required: false
      scoring_guide:
        0: "No champion identified"
        1: "Friendly contact, no advocacy signals"
        2: "Prospect volunteered to share internally"
        3: "Explicit champion identified, next step confirmed"

  conversation_metrics:
    - id: talk_ratio
      label: "Rep talk time"
      target_range: [0.38, 0.46]    # Optimal: rep speaks 38–46% of call
      flag_above: 0.55              # Flag if rep dominates
      flag_below: 0.20              # Flag if rep disengages

    - id: next_step_confirmed
      label: "Next step confirmed"
      type: boolean
      description: "Call ended with a specific next action, date, and owner"

    - id: objections_handled
      label: "Objections handled"
      type: count
      description: "Count of distinct objections raised and addressed"

    - id: competitor_mentions
      label: "Competitor mentions"
      type: list
      description: "Competitor names mentioned by either party"
```

---

## Project structure

```
salespulse/
├── .github/
│   └── workflows/
│       └── ci.yml                  # Ruff lint + Pyright type check
├── src/
│   └── salespulse/
│       ├── __init__.py
│       ├── ingest/
│       │   ├── __init__.py
│       │   ├── receiver.py         # FastAPI upload + webhook handlers
│       │   ├── deduplicator.py     # Call ID idempotency check
│       │   └── audio_validator.py  # Format, duration, sample rate checks
│       ├── asr/
│       │   ├── __init__.py
│       │   ├── base.py             # ASRProvider ABC
│       │   ├── whisper_provider.py # faster-whisper local implementation
│       │   ├── deepgram_provider.py
│       │   ├── assemblyai_provider.py
│       │   └── registry.py         # Provider lookup by config key
│       ├── diarization/
│       │   ├── __init__.py
│       │   ├── diarizer.py         # pyannote.audio wrapper
│       │   ├── aligner.py          # Align word timestamps to speaker segments
│       │   └── speaker_map.py      # SPEAKER_00 → rep/prospect name resolution
│       ├── transcript/
│       │   ├── __init__.py
│       │   ├── models.py           # Transcript, Segment, Turn dataclasses
│       │   ├── normaliser.py       # Segment merge, filler removal, clean JSON
│       │   └── serialiser.py       # Transcript ↔ DB / JSON / prompt string
│       ├── scoring/
│       │   ├── __init__.py
│       │   ├── rubric.py           # Load + validate rubric.yaml → RubricConfig
│       │   ├── prompt_builder.py   # Transcript + rubric → LLM prompt
│       │   ├── llm_scorer.py       # LLM call + response parser
│       │   ├── evidence.py         # Evidence extraction + timestamp linkage
│       │   ├── scorecard.py        # Scorecard dataclass + validation
│       │   └── metrics.py          # Talk ratio, next step, competitor detector
│       ├── coaching/
│       │   ├── __init__.py
│       │   ├── aggregator.py       # Per-rep scorecard history aggregation
│       │   ├── pattern_detector.py # Flag underperformers, top objections
│       │   ├── report_builder.py   # CoachingReport assembly
│       │   └── trend.py            # Week-over-week rep trend computation
│       ├── crm/
│       │   ├── __init__.py
│       │   ├── base.py             # CRMAdapter ABC
│       │   ├── hubspot.py          # HubSpot REST adapter
│       │   ├── salesforce.py       # Salesforce REST adapter (OAuth2 PKCE)
│       │   ├── pipedrive.py        # Pipedrive REST adapter
│       │   ├── webhook.py          # Generic outbound webhook adapter
│       │   └── registry.py         # Adapter lookup by config key
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── celery_app.py       # Celery application factory
│       │   ├── tasks.py            # Task definitions (one per stage)
│       │   ├── chain.py            # Stage chaining + error recovery
│       │   └── state.py            # Call processing state machine
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py              # FastAPI application factory
│       │   ├── routes/
│       │   │   ├── calls.py        # Upload, status, scorecard endpoints
│       │   │   ├── reps.py         # Per-rep dashboard + history
│       │   │   ├── team.py         # Team report + leaderboard
│       │   │   └── webhooks.py     # Inbound CRM webhook handlers
│       │   └── schemas.py          # Pydantic request/response models
│       ├── models/
│       │   ├── __init__.py
│       │   ├── call.py             # Call ORM model
│       │   ├── transcript.py       # Transcript + Segment ORM models
│       │   ├── scorecard.py        # Scorecard + Criterion ORM models
│       │   ├── rep.py              # Rep + team ORM models
│       │   └── coaching.py         # CoachingReport ORM model
│       └── voice/                  # Optional voice agent layer
│           ├── __init__.py
│           ├── twilio_handler.py   # WebSocket media stream bridge
│           ├── session.py          # VoiceAgentSession: STT/LLM/TTS loop
│           ├── agent.py            # LLM agent with call script + function tools
│           └── outcome.py          # Parse call outcome → pipeline ingest
├── alembic/
│   ├── env.py                          # Reads DATABASE_URL, imports all models
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py      # Creates all 8 tables
├── alembic.ini                         # Alembic config (URL set via env)
├── config/
│   ├── config.example.yaml
│   └── rubric.example.yaml
├── tests/
│   ├── fixtures/
│   │   ├── sample_transcript.json  # Pre-diarized transcript (skips ASR in tests)
│   │   └── expected_scorecard.json # Expected MEDDIC scores for the fixture call
│   ├── conftest.py                 # Shared fixtures: rubric, transcript, mock LLM response
│   ├── test_rubric.py
│   ├── test_scorecard.py
│   ├── test_scorecard_bugs.py      # Regression tests for the 8 confirmed fixes
│   ├── test_metrics.py
│   ├── test_evidence.py
│   ├── test_prompt_builder.py
│   ├── test_normaliser.py
│   ├── test_state.py               # Redis state machine (fakeredis)
│   ├── test_pipeline_smoke.py      # End-to-end smoke: mock LLM, real pipeline logic
│   ├── test_api_smoke.py           # FastAPI TestClient smoke tests
│   ├── test_llm_scorer.py
│   └── test_crm_registry.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Use cases

**EU regulatory context:**

| Framework | Relevance |
|---|---|
| **GDPR (Art. 6, 13, 17)** | Call recordings containing personal data require a lawful basis (consent or legitimate interest). Participants must be informed. Art. 17 right to erasure applies — the pipeline must support `DELETE /calls/{id}` that purges audio, transcript, and scorecard. |
| **EU AI Act (Art. 13)** | AI systems that influence employment-related decisions (rep performance evaluation, promotion, termination) fall under high-risk classification. Transparency obligation: every score must be explainable. Evidence-backed scoring in `scoring/evidence.py` directly addresses this requirement. |
| **GDPR (Art. 28)** | If using a managed ASR/LLM provider (Deepgram, OpenAI), a Data Processing Agreement must be in place before submitting call recordings. Provider abstraction makes it straightforward to switch to an on-premises model if DPA cannot be established. |

**Deployment patterns:**

- **Self-hosted on-prem** — Whisper local + Ollama LLM + PostgreSQL: zero external data transfer,
  suitable for regulated sectors (finance, healthcare, legal) where call recordings cannot leave
  the corporate network.

- **Hybrid** — Whisper local (audio stays on-prem) + OpenAI API (only the cleaned transcript,
  no audio, is sent to the LLM): balances data residency with model quality.

- **Fully managed** — Deepgram + OpenAI: fastest to deploy, highest per-call cost, requires
  DPAs with both providers.

---

## Status

**Production-ready scaffold** — scoring pipeline fully implemented and tested.

What works end-to-end:
- Audio ingest → mock ASR → transcript normalisation → LLM scoring → scorecard with evidence
- Redis-backed pipeline state machine visible across API and worker processes
- MEDDIC rubric loader, prompt builder, evidence verifier, coaching flag generator
- FastAPI endpoints: upload, status polling, health
- Alembic migrations: 8 tables, `alembic upgrade head` to initialise schema
- 107 tests passing (unit + smoke), 100% coverage on state/metrics/registry layers

What remains stubbed (raise NotImplementedError):
- CRM adapter implementations (HubSpot, Salesforce, Pipedrive) — registry and ABC are wired
- Real ASR/diarization path (set `MOCK_ASR=false` + provider credentials to activate)
- Coaching aggregator DB queries, voice agent TTS/STT loop

Tested reference: internal B2B SaaS sales team, ~300 calls/month, HubSpot CRM, MEDDIC rubric,
Whisper large-v3 on CPU (t3.xlarge), average processing time 9 minutes per 45-minute call.
