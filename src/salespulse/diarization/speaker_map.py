"""
diarization/speaker_map.py

Resolves anonymous speaker IDs (SPEAKER_00, SPEAKER_01) to semantic
role labels (rep, prospect) or real names.

Resolution strategies (in priority order):
  1. Explicit config map: speaker_name_map in config.yaml
  2. Heuristic: the speaker with the lower talk ratio is usually the prospect
     in a well-run discovery call (rep talks 38–46% of call time)
  3. Fallback: SPEAKER_00 → "rep", SPEAKER_01 → "prospect"

Interface:
    resolve_speakers(segments, config) -> dict[str, str]
"""

from __future__ import annotations

from dataclasses import dataclass

from .diarizer import DiarizedSegment


@dataclass
class SpeakerMapConfig:
    """
    Maps raw diarization labels to semantic names.
    Loaded from config.yaml `diarization.speaker_name_map`.
    """
    explicit_map: dict[str, str]        # e.g. {"SPEAKER_00": "rep"}
    use_heuristic: bool = True          # Fall back to talk-ratio heuristic


def resolve_speakers(
    segments: list[DiarizedSegment],
    config: SpeakerMapConfig,
) -> dict[str, str]:
    """
    Return a mapping from anonymous speaker IDs to semantic role names.

    Args:
        segments: Diarized segments with speaker_id and timing.
        config: Resolution config (explicit map + heuristic flag).

    Returns:
        Dict like {"SPEAKER_00": "rep", "SPEAKER_01": "prospect"}.
        All speaker_ids present in `segments` will have an entry.
    """
    raise NotImplementedError


def compute_talk_ratios(segments: list[DiarizedSegment]) -> dict[str, float]:
    """
    Compute each speaker's fraction of total talk time.

    Args:
        segments: Diarized segments.

    Returns:
        Dict like {"SPEAKER_00": 0.42, "SPEAKER_01": 0.58}.
        Values sum to approximately 1.0.
    """
    raise NotImplementedError
