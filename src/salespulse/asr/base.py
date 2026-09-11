"""
asr/base.py

Abstract base class for all ASR (Automatic Speech Recognition) providers.

Concrete implementations:
  - WhisperLocalProvider  (faster-whisper, runs on-prem)
  - DeepgramProvider      (Deepgram Nova-2 API)
  - AssemblyAIProvider    (AssemblyAI Universal-2 API)

Interface:
    ASRProvider.transcribe(path, config) -> RawTranscript
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WordToken:
    """A single recognised word with timing metadata."""
    word: str
    start: float      # seconds from call start
    end: float
    confidence: float  # 0.0 – 1.0


@dataclass
class RawTranscript:
    """
    Provider-agnostic output from ASR. Contains word-level tokens but
    no speaker information — diarization is a separate stage.
    """
    text: str
    words: list[WordToken]
    language: str        # ISO 639-1 detected language
    duration: float      # total audio duration in seconds
    provider: str        # name of the provider that produced this


@dataclass
class ASRConfig:
    language: str | None = None   # None = auto-detect
    model: str = "large-v3"
    compute_type: str = "int8"    # float32 | int8


class ASRProvider(ABC):
    """
    Transcribe an audio file and return word-level tokens.
    Implementations must be stateless (or manage their own state).
    """

    @abstractmethod
    def transcribe(self, path: Path, config: ASRConfig) -> RawTranscript:
        """
        Transcribe the audio file at `path`.

        Args:
            path: Path to the 16 kHz mono WAV file.
            config: ASR configuration (model, language, compute type).

        Returns:
            RawTranscript with word-level tokens and confidence scores.

        Raises:
            ASRError: On provider failure or invalid audio.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Short identifier used in logs and the RawTranscript.provider field."""
        raise NotImplementedError


class ASRError(Exception):
    """Raised when the ASR provider fails to transcribe."""
    pass
