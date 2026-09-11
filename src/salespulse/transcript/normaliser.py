"""
transcript/normaliser.py

Converts a JSON fixture or attributed words into a canonical Transcript.
In the mock pipeline, loads from sample_transcript.json directly.

Interface:
    normalise_from_fixture(fixture_path, call_id) -> Transcript
    normalise(words, speaker_map, config, call_id, language, duration) -> Transcript
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from .models import Transcript, Turn, Word


MAX_SILENCE_S = 1.0

FILLER_WORDS = frozenset({
    "uh", "um", "er", "ah", "hmm",
})


@dataclass
class NormaliserConfig:
    strip_fillers: bool = True
    max_silence_merge_seconds: float = MAX_SILENCE_S
    asr_provider: str = "mock"


def normalise_from_fixture(fixture_path: Path, call_id: UUID) -> Transcript:
    """
    Load a pre-built transcript fixture (JSON) and return a Transcript.
    Used in the mock pipeline to skip ASR and diarization.

    Args:
        fixture_path: Path to sample_transcript.json
        call_id: UUID to assign to the Transcript.

    Returns:
        Transcript domain model.
    """
    with open(fixture_path) as f:
        data = json.load(f)

    turns = []
    for t in data.get("turns", []):
        words = [
            Word(
                text=w["word"],
                start=w["start"],
                end=w["end"],
                confidence=w.get("confidence", 1.0),
                speaker=t["speaker"],
            )
            for w in t.get("words", [])
        ]
        turns.append(Turn(
            speaker=t["speaker"],
            start=t["start"],
            end=t["end"],
            text=t["text"],
            words=words,
        ))

    return Transcript(
        call_id=call_id,
        turns=turns,
        language=data.get("language", "en"),
        duration_seconds=data.get("duration_seconds", 0.0),
        asr_provider=data.get("asr_provider", "mock"),
        rep_speaker_id=data.get("rep_speaker_id", "rep"),
    )


def normalise(
    words,  # list[AttributedWord]
    speaker_map: dict[str, str],
    config: NormaliserConfig,
    call_id: UUID,
    language: str,
    duration_seconds: float,
) -> Transcript:
    """
    Build a Transcript from attributed words (real ASR + diarization path).
    """
    # Group into turns
    grouped = _group_into_turns(words, speaker_map, config.max_silence_merge_seconds)

    turns = []
    for speaker, attributed_words in grouped:
        if not attributed_words:
            continue

        word_objects = []
        for aw in attributed_words:
            text = aw.word
            if config.strip_fillers and text.lower() in FILLER_WORDS:
                continue
            word_objects.append(Word(
                text=text,
                start=aw.start,
                end=aw.end,
                confidence=aw.confidence,
                speaker=speaker,
            ))

        if not word_objects:
            continue

        turn_text = " ".join(w.text for w in word_objects)
        turns.append(Turn(
            speaker=speaker,
            start=attributed_words[0].start,
            end=attributed_words[-1].end,
            text=turn_text,
            words=word_objects,
        ))

    return Transcript(
        call_id=call_id,
        turns=turns,
        language=language,
        duration_seconds=duration_seconds,
        asr_provider=config.asr_provider,
        rep_speaker_id="rep",
    )


def _group_into_turns(words, speaker_map, max_silence_s):
    """Group adjacent same-speaker words into (speaker, words) tuples."""
    if not words:
        return []

    groups: list[tuple[str, list]] = []
    current_speaker = speaker_map.get(words[0].speaker_id, words[0].speaker_id)
    current_group = [words[0]]

    for word in words[1:]:
        speaker = speaker_map.get(word.speaker_id, word.speaker_id)
        gap = word.start - current_group[-1].end

        if speaker == current_speaker and gap <= max_silence_s:
            current_group.append(word)
        else:
            groups.append((current_speaker, current_group))
            current_speaker = speaker
            current_group = [word]

    groups.append((current_speaker, current_group))
    return groups
