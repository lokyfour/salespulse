"""
api/app.py

FastAPI application factory.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title="salespulse",
        description="AI sales quality agent — transcribe, score, coach, sync",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Upload endpoint ──────────────────────────────────────────────────
    @app.post("/calls/upload")
    async def upload_call(
        background: BackgroundTasks,
        file: UploadFile = File(...),
        rep_id: str = Form(...),
        crm_deal_id: str | None = Form(None),
    ):
        """
        Accept an audio file, save to /tmp, enqueue pipeline.
        Returns call_id immediately.
        """
        suffix = Path(file.filename or "call.mp3").suffix or ".mp3"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        contents = await file.read()
        await asyncio.to_thread(Path(tmp_path).write_bytes, contents)
        background.add_task(os.unlink, tmp_path)

        from ..pipeline.tasks import enqueue_call
        call_id = enqueue_call(
            audio_path=tmp_path,
            rep_id=rep_id,
            crm_deal_id=crm_deal_id,
        )
        return {"call_id": call_id, "status": "queued"}

    # ── Status endpoint ──────────────────────────────────────────────────
    @app.get("/calls/{call_id}/status")
    async def get_call_status(call_id: str):
        from ..pipeline.tasks import get_call_result
        result = get_call_result(call_id)
        if "error" in result and result["error"] == "call_not_found":
            raise HTTPException(status_code=404, detail="Call not found")
        return result

    # ── Health endpoint ──────────────────────────────────────────────────
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
