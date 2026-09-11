"""
voice/agent.py

LLM-powered voice agent with call script and function-calling tools.

The agent runs a goal-directed sales conversation using the configured
call script as its system prompt. Function-calling tools allow it to
take real actions during the call without waiting for the call to end:

  Tools available to the agent:
    book_appointment(date, time, timezone) → confirmation_id
    leave_voicemail_signal()               → triggers voicemail mode
    flag_not_interested()                  → ends call gracefully
    flag_callback_requested(callback_time) → schedules follow-up

The LLM is not given full conversation history every turn — only the
last N turns plus a structured state summary. This keeps latency low
and avoids context length issues on long calls.

Interface:
    VoiceAgent(config)
    agent.respond(utterance, session_state) -> AgentResponse
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CallOutcomeSignal(StrEnum):
    CONTINUE = "continue"
    APPOINTMENT_BOOKED = "appointment_booked"
    VOICEMAIL = "voicemail"
    NOT_INTERESTED = "not_interested"
    CALLBACK_REQUESTED = "callback_requested"
    MAX_DURATION = "max_duration"


@dataclass
class AgentConfig:
    """Configuration for one outbound call campaign."""

    call_script: str  # System prompt defining agent persona and goal
    max_turns: int = 20  # Hard cap on conversation turns
    llm_model: str = "gpt-4o"
    tts_provider: str = "elevenlabs"
    tts_voice_id: str = ""
    available_tools: list[str] = None  # Tool names to enable


@dataclass
class AgentResponse:
    """Output of one agent turn."""

    text: str  # Text to synthesise
    outcome_signal: CallOutcomeSignal  # What the agent decided
    tool_called: str | None = None  # Tool name if a tool was invoked
    tool_result: dict | None = None  # Tool execution result


@dataclass
class SessionState:
    """Compact state summary passed to the LLM each turn."""

    turn_count: int
    prospect_name: str
    outcome_signals_so_far: list[CallOutcomeSignal]
    recent_history: list[dict]  # Last 6 turns [{role, content}]


class VoiceAgent:
    """
    Stateless LLM agent. Receives utterance + session state, returns response.
    State management is the responsibility of VoiceAgentSession.
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config

    def respond(
        self,
        utterance: str,
        state: SessionState,
    ) -> AgentResponse:
        """
        Generate the agent's next response.

        Builds the LLM prompt from the call script, recent history, and
        the prospect's latest utterance. Parses the response for tool
        calls and outcome signals.

        Args:
            utterance: The prospect's most recent utterance (from STT).
            state: Current session state summary.

        Returns:
            AgentResponse with text and outcome signal.
        """
        raise NotImplementedError

    def _build_messages(
        self,
        utterance: str,
        state: SessionState,
    ) -> list[dict]:
        """Build the messages list for the LLM API call."""
        raise NotImplementedError

    def _parse_tool_calls(self, response: dict) -> AgentResponse:
        """Extract tool calls and outcome signals from LLM response."""
        raise NotImplementedError
