"""
diarization/aligner.py

Aligns word-level tokens from ASR with speaker segments from diarization.

Problem: ASR produces words with timestamps; diarization produces speaker
segments with timestamps. These two time series must be merged into a
single speaker-attributed word list.

Strategy: for each word, find the diarized segment with the highest
time overlap. Words at segment boundaries are assigned to the segment
covering their midpoint.

Interface:
    align(words, segments) -> list[AttributedWord]
"""

from __future__ import annotations

from dataclasses import dataclass

from ..asr.base import WordToken
from .diarizer import DiarizedSegment


@dataclass
class AttributedWord:
    """A single word with speaker attribution and timing."""
    word: str
    start: float
    end: float
    confidence: float
    speaker_id: str   # "SPEAKER_00" | "SPEAKER_01" | "unknown"


def align(
    words: list[WordToken],
    segments: list[DiarizedSegment],
) -> list[AttributedWord]:
    """
    Assign each word in `words` to the speaker in `segments` whose
    time interval covers the word's midpoint.

    Words that fall outside all diarized segments receive speaker_id="unknown".

    Args:
        words: Word-level tokens from ASR (sorted by start time).
        segments: Speaker segments from diarization (sorted by start time).

    Returns:
        List of AttributedWord, preserving original word order.
    """
    raise NotImplementedError
