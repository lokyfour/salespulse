"""
diarization/diarizer.py

Speaker diarization using pyannote.audio 3.1.

Assigns anonymous speaker labels (SPEAKER_00, SPEAKER_01, ...) to
time segments. Labels are later resolved to real names by speaker_map.py.

Known limitation: overlapping speech (two speakers simultaneously) is
not reliably handled — pyannote assigns one label per segment.
This is a recognised open problem in the open-source diarization space.

Interface:
    Diarizer.diarize(path, config) -> list[DiarizedSegment]
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DiarizedSegment:
    """A time segment attributed to a single speaker."""
    speaker_id: str   # "SPEAKER_00", "SPEAKER_01", etc.
    start: float      # seconds
    end: float


@dataclass
class DiarizationConfig:
    min_speakers: int = 2
    max_speakers: int = 4
    # Path to a HuggingFace token file — required for pyannote model download
    hf_token: str | None = None


class Diarizer:
    """
    pyannote.audio wrapper.

    The pyannote pipeline is loaded once and reused. Requires a
    HuggingFace token with access to pyannote/speaker-diarization-3.1.
    """

    def __init__(self, hf_token: str | None = None) -> None:
        """
        Args:
            hf_token: HuggingFace API token for model download.
        """
        self._hf_token = hf_token
        self._pipeline = None  # Loaded lazily

    def diarize(
        self,
        path: Path,
        config: DiarizationConfig,
    ) -> list[DiarizedSegment]:
        """
        Run speaker diarization on the audio at `path`.

        Args:
            path: Path to 16 kHz mono WAV.
            config: Number-of-speakers constraints.

        Returns:
            List of DiarizedSegments sorted by start time.
        """
        raise NotImplementedError

    def _load_pipeline(self) -> None:
        """Load the pyannote pipeline. Called once, cached in self._pipeline."""
        raise NotImplementedError
