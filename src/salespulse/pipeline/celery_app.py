"""
pipeline/celery_app.py

Celery application factory.
"""

from __future__ import annotations

import os
from celery import Celery


def create_celery_app() -> Celery:
    broker = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    backend = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    app = Celery("salespulse", broker=broker, backend=backend)

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        result_expires=86400,
        task_routes={
            "salespulse.transcribe_audio": {"queue": "asr"},
            "salespulse.diarize_audio": {"queue": "diarize"},
            "salespulse.normalise_transcript": {"queue": "score"},
            "salespulse.score_transcript": {"queue": "score"},
            "salespulse.generate_coaching": {"queue": "coaching"},
            "salespulse.push_to_crm": {"queue": "crm_push"},
        },
        task_acks_late=True,          # Re-queue task if worker dies mid-execution
        worker_prefetch_multiplier=1, # One task at a time for CPU-heavy ASR worker
    )

    # Auto-discover tasks in pipeline.tasks
    app.autodiscover_tasks(["salespulse.pipeline"])
    return app


app = create_celery_app()
