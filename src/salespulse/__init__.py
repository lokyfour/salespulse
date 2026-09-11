"""
salespulse

AI sales quality agent — transcribe, score, coach, sync.

Pipeline stages:
    ingest → asr → diarization → transcript → scoring → coaching → crm

Entry points:
    salespulse.api.app:create_app()       FastAPI application
    salespulse.pipeline.celery_app:app    Celery application
"""

__version__ = "0.1.0"
