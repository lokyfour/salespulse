"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-09-11

Tables created:
    calls               — root call record + pipeline state machine
    transcripts         — one per call, language/duration/provider metadata
    turns               — speaker turns with word-level JSONB
    scorecards          — one per call, overall score + conversation metrics
    criterion_scores    — one per rubric criterion per call
    reps                — lightweight rep identity record
    coaching_reports    — one per rep, updated after every scored call
    call_dedup_keys     — idempotency table for ingest deduplication
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── calls ────────────────────────────────────────────────────────────
    op.create_table(
        "calls",
        sa.Column("call_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rep_id", sa.String(255), nullable=False),
        sa.Column("team_id", sa.String(255), nullable=True),
        sa.Column("crm_deal_id", sa.String(255), nullable=True),
        sa.Column("crm_type", sa.String(50), nullable=True),
        sa.Column("stage", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("failed_at_stage", sa.String(50), nullable=True),
        sa.Column("error_message", sa.String(2048), nullable=True),
        sa.Column("audio_path", sa.String(1024), nullable=True),
        sa.Column("audio_duration_seconds", sa.Float, nullable=True),
        sa.Column("asr_provider", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("erased_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_calls_rep_id", "calls", ["rep_id"])
    op.create_index("ix_calls_team_id", "calls", ["team_id"])
    op.create_index("ix_calls_stage", "calls", ["stage"])

    # ── transcripts ──────────────────────────────────────────────────────
    op.create_table(
        "transcripts",
        sa.Column("transcript_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calls.call_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("duration_seconds", sa.Float, nullable=False),
        sa.Column("asr_provider", sa.String(50), nullable=False),
        sa.Column("rep_speaker_id", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_transcripts_call_id", "transcripts", ["call_id"])

    # ── turns ────────────────────────────────────────────────────────────
    op.create_table(
        "turns",
        sa.Column("turn_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "transcript_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transcripts.transcript_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("speaker", sa.String(100), nullable=False),
        sa.Column("start", sa.Float, nullable=False),
        sa.Column("end", sa.Float, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("words", postgresql.JSONB, nullable=True),
    )
    op.create_index("ix_turns_transcript_id", "turns", ["transcript_id"])

    # ── scorecards ───────────────────────────────────────────────────────
    op.create_table(
        "scorecards",
        sa.Column("scorecard_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calls.call_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("rubric_name", sa.String(255), nullable=False),
        sa.Column("rubric_version", sa.String(50), nullable=False),
        sa.Column("overall_score", sa.Integer, nullable=False),
        sa.Column("talk_ratio", sa.Float, nullable=False),
        sa.Column("next_step_confirmed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("objections_handled", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "competitor_mentions",
            postgresql.ARRAY(sa.String),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("overall_notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_scorecards_call_id", "scorecards", ["call_id"])

    # ── criterion_scores ─────────────────────────────────────────────────
    op.create_table(
        "criterion_scores",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "scorecard_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scorecards.scorecard_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("criterion_id", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("weight", sa.Integer, nullable=False),
        sa.Column("evidence", sa.Text, nullable=True),
        sa.Column("evidence_timestamp", sa.String(20), nullable=True),
        sa.Column("flag", sa.String(100), nullable=True),
    )
    op.create_index("ix_criterion_scores_scorecard_id", "criterion_scores", ["scorecard_id"])

    # ── reps ─────────────────────────────────────────────────────────────
    op.create_table(
        "reps",
        sa.Column("rep_id", sa.String(255), primary_key=True),
        sa.Column("team_id", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("crm_contact_id", sa.String(255), nullable=True),
        sa.Column("crm_type", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_reps_team_id", "reps", ["team_id"])

    # ── coaching_reports ─────────────────────────────────────────────────
    op.create_table(
        "coaching_reports",
        sa.Column("rep_id", sa.String(255), primary_key=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("calls_analysed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("average_overall_score", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "score_trend_direction",
            sa.String(20),
            nullable=False,
            server_default="stable",
        ),
        sa.Column("top_strength", sa.String(100), nullable=True),
        sa.Column("top_weakness", sa.String(100), nullable=True),
        sa.Column("flags", postgresql.JSONB, nullable=True),
        sa.Column("recommended_actions", postgresql.JSONB, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── call_dedup_keys ──────────────────────────────────────────────────
    # Idempotency table — prevents the same recording from entering the
    # pipeline twice regardless of source (file hash, CRM deal ID, Twilio SID).
    op.create_table(
        "call_dedup_keys",
        sa.Column("dedup_key", sa.String(512), primary_key=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calls.call_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("call_dedup_keys")
    op.drop_table("coaching_reports")
    op.drop_table("reps")
    op.drop_table("criterion_scores")
    op.drop_table("scorecards")
    op.drop_table("turns")
    op.drop_table("transcripts")
    op.drop_table("calls")
