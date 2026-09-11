"""
asr/deepgram_provider.py

Managed ASR provider using the Deepgram Nova-2 API.

Sends audio to Deepgram's cloud endpoint. A Data Processing Agreement
must be in place before using this provider in EU deployments (GDPR Art. 28).

Deepgram Nova-2 advantages over Whisper local:
  - Lower WER on accented English and technical vocabulary
  - Built-in diarization (can replace the diarization stage for simple cases)
  - Processing time: ~10–20 seconds per hour of audio

Interface:
    DeepgramProvider.transcribe(path, config) -> RawTranscript
"""

from __future__ import annotations

from pathlib import Path

from .base import ASRConfig, ASRProvider, RawTranscript


class DeepgramProvider(ASRProvider):
    """
    Deepgram REST API wrapper (Nova-2 model, pre-recorded endpoint).

    Requires DEEPGRAM_API_KEY in environment or passed to constructor.
    """

    def __init__(self, api_key: str) -> None:
        """
        Args:
            api_key: Deepgram API key.
        """
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "deepgram"

    def transcribe(self, path: Path, config: ASRConfig) -> RawTranscript:
        """
        Upload `path` to Deepgram pre-recorded transcription endpoint.

        Requests word-level timestamps (punctuate=true, words=true).
        Language detection is automatic unless config.language is set.

        Args:
            path: Path to local audio file (any format Deepgram accepts).
            config: ASR config (language, model variant if applicable).

        Returns:
            RawTranscript normalised from Deepgram's JSON response.

        Raises:
            ASRError: On HTTP error or malformed response.
        """
        raise NotImplementedError
