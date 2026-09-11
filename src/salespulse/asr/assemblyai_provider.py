"""
asr/assemblyai_provider.py

Managed ASR provider using the AssemblyAI Universal-2 API.

AssemblyAI uses an async polling model: the file is uploaded, a
transcription job is submitted, and the caller polls until complete.
This module handles the full upload → poll → retrieve cycle.

Interface:
    AssemblyAIProvider.transcribe(path, config) -> RawTranscript
"""

from __future__ import annotations

from pathlib import Path

from .base import ASRConfig, ASRProvider, RawTranscript

ASSEMBLYAI_UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
ASSEMBLYAI_TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 120  # 10 minutes before timeout


class AssemblyAIProvider(ASRProvider):
    """
    AssemblyAI REST API wrapper (Universal-2 model).

    Requires ASSEMBLYAI_API_KEY in environment or passed to constructor.
    """

    def __init__(self, api_key: str) -> None:
        """
        Args:
            api_key: AssemblyAI API key.
        """
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "assemblyai"

    def transcribe(self, path: Path, config: ASRConfig) -> RawTranscript:
        """
        Submit `path` to AssemblyAI and poll until the transcript is ready.

        Stages:
          1. Upload audio → receive upload_url
          2. Submit transcript job with upload_url → receive transcript_id
          3. Poll GET /transcript/{id} until status == "completed"
          4. Parse words[] into WordToken list

        Args:
            path: Path to local audio file.
            config: ASR config.

        Returns:
            RawTranscript from AssemblyAI response.

        Raises:
            ASRError: On upload failure, job error, or timeout.
        """
        raise NotImplementedError

    def _upload(self, path: Path) -> str:
        """Upload audio file and return the AssemblyAI upload URL."""
        raise NotImplementedError

    def _submit_job(self, upload_url: str, config: ASRConfig) -> str:
        """Submit a transcription job and return the transcript_id."""
        raise NotImplementedError

    def _poll(self, transcript_id: str) -> dict:
        """Poll until transcript is complete. Return the full response dict."""
        raise NotImplementedError
