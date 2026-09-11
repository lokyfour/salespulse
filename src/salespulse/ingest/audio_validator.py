"""
ingest/audio_validator.py

Validates an audio file before it enters the pipeline.

Checks performed:
  - MIME type / file extension: mp3, wav, ogg, m4a, flac, webm
  - File size: configurable max (default 500 MB)
  - Duration: configurable max (default 120 minutes)
  - Sample rate: resampled to 16 kHz if needed (Whisper requirement)
  - Corruption: basic container integrity check

Interface:
    AudioValidator.validate(path: Path, config: AudioConfig) -> ValidationResult
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_FORMATS = {"mp3", "wav", "ogg", "m4a", "flac", "webm"}


@dataclass
class AudioConfig:
    max_size_mb: int = 500
    max_duration_minutes: int = 120
    target_sample_rate: int = 16_000


@dataclass
class ValidationResult:
    valid: bool
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None
    rejection_reason: str | None  # None when valid=True


class AudioValidator:
    """
    Stateless validator. Uses pydub / ffprobe to inspect audio metadata
    without fully decoding the file.
    """

    def validate(
        self,
        path: Path,
        config: AudioConfig,
    ) -> ValidationResult:
        """
        Validate the audio file at `path` against `config` constraints.

        Args:
            path: Path to the audio file on disk.
            config: Validation thresholds.

        Returns:
            ValidationResult. Check `valid` before proceeding.
        """
        raise NotImplementedError

    def resample_if_needed(
        self,
        path: Path,
        target_sample_rate: int,
        output_path: Path,
    ) -> Path:
        """
        Resample audio to `target_sample_rate` if the source differs.
        Returns `path` unchanged if no resampling is required.

        Args:
            path: Source audio path.
            target_sample_rate: Target sample rate in Hz (e.g. 16000).
            output_path: Destination for resampled file.

        Returns:
            Path to the (possibly resampled) file.
        """
        raise NotImplementedError
