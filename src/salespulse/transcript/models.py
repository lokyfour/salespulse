"""
transcript/models.py

Domain models for the canonical transcript representation.

Models:
    Word         — single word with timing and speaker
    Turn         — contiguous speaker turn (sequence of words)
    Transcript   — complete call transcript with metadata
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class Word:
    text: str
    start: float
    end: float
    confidence: float
    speaker: str


@dataclass
class Turn:
    speaker: str
    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def word_count(self) -> int:
        return len(self.words)


@dataclass
class Transcript:
    call_id: UUID
    turns: list[Turn]
    language: str
    duration_seconds: float
    asr_provider: str
    rep_speaker_id: str

    @property
    def rep_turns(self) -> list[Turn]:
        return [t for t in self.turns if t.speaker == self.rep_speaker_id]

    @property
    def prospect_turns(self) -> list[Turn]:
        return [t for t in self.turns if t.speaker != self.rep_speaker_id]

    @property
    def rep_talk_ratio(self) -> float:
        rep_time = sum(t.duration for t in self.rep_turns)
        return round(rep_time / self.duration_seconds, 3) if self.duration_seconds > 0 else 0.0

    def as_prompt_string(self) -> str:
        """
        Render as timestamped dialogue for LLM input.
        Format: [MM:SS] SPEAKER: text
        """
        lines = []
        for turn in self.turns:
            minutes = int(turn.start // 60)
            seconds = int(turn.start % 60)
            label = "REP" if turn.speaker == self.rep_speaker_id else "PROSPECT"
            lines.append(f"[{minutes:02d}:{seconds:02d}] {label}: {turn.text}")
        return "\n".join(lines)
