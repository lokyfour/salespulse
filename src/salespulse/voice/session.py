"""
voice/session.py

Real-time STT → LLM → TTS loop for a single outbound call.

Architecture:
  Audio in (from Twilio WebSocket)
    → streaming STT (Deepgram streaming API)
    → transcript buffer (per-utterance)
    → LLM agent (on utterance complete)
    → TTS (ElevenLabs / Google / Azure)
    → Audio out (to Twilio WebSocket)

Key engineering constraints:
  - Total response latency target: < 800 ms (STT + LLM + TTS)
  - LLM must use streaming output → TTS begins before LLM finishes
  - Interruption handling: if prospect speaks while agent is talking,
    drain the TTS buffer and hand back to STT immediately
  - State is centralised in VoiceAgentSession, not in LLM context
    (LLM context window is rebuilt each turn from session.history)

Interface:
    VoiceAgentSession(call_sid, agent_config)
    session.feed_audio(pcm_chunk) -> bytes | None   # Returns TTS audio or None
    session.finalise() -> SessionResult
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .agent import AgentConfig, VoiceAgent
from .outcome import SessionResult


@dataclass
class VoiceAgentSession:
    """
    Stateful session for one outbound call.

    Holds the conversation history, manages the STT/LLM/TTS loop,
    and tracks call outcome signals (appointment booked, voicemail, etc.).
    """

    call_sid: str
    agent_config: AgentConfig
    history: list[dict] = field(default_factory=list)  # [{role, content}]
    is_active: bool = False
    _agent: VoiceAgent | None = None

    def start(self, lead_data: dict) -> None:
        """
        Initialise the session with lead data and start the STT stream.

        The agent's opening line is generated from lead_data (name,
        company, product context) so the first thing the prospect hears
        is personalised.

        Args:
            lead_data: Dict with prospect name, company, context fields.
        """
        raise NotImplementedError

    def feed_audio(self, pcm_chunk: bytes) -> bytes | None:
        """
        Feed a PCM audio chunk into the STT stream.

        If the STT detects end-of-utterance, runs the LLM agent and
        returns TTS audio bytes for the agent's response.
        Returns None if the utterance is not yet complete.

        Args:
            pcm_chunk: Raw PCM 16-bit bytes from Twilio.

        Returns:
            TTS audio bytes if a response is ready, None otherwise.
        """
        raise NotImplementedError

    def handle_interruption(self) -> None:
        """
        Called when the prospect speaks while the agent is talking.
        Stops TTS playback and returns control to STT.
        """
        raise NotImplementedError

    def finalise(self) -> SessionResult:
        """
        End the session, extract call outcome, and return a SessionResult
        suitable for ingestion into the main scoring pipeline.

        Returns:
            SessionResult with transcript, outcome, and call metadata.
        """
        raise NotImplementedError
