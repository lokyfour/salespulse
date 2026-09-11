"""
voice/twilio_handler.py

WebSocket media stream bridge between Twilio and the voice agent session.

Twilio streams μ-law encoded audio over a WebSocket connection established
at the /voice/stream endpoint. This handler:
  1. Accepts the WebSocket upgrade from Twilio
  2. Decodes μ-law audio chunks → PCM 16-bit 8 kHz
  3. Passes audio to VoiceAgentSession for real-time STT/LLM/TTS
  4. Sends TTS audio back to Twilio over the same WebSocket
  5. On call end, forwards the call transcript to the main pipeline

Twilio sends JSON-framed messages:
  {"event": "start",   "streamSid": "...", "callSid": "..."}
  {"event": "media",   "media": {"payload": "<base64 mulaw>"}}
  {"event": "stop",    "streamSid": "..."}

Interface:
    handle_stream(websocket) -> None   (called by FastAPI route)
"""

from __future__ import annotations

from fastapi import WebSocket


async def handle_stream(websocket: WebSocket) -> None:
    """
    Main WebSocket handler for a Twilio media stream.

    Lifecycle:
      1. Accept WebSocket connection
      2. Wait for "start" event → extract callSid, streamSid
      3. Create VoiceAgentSession for this call
      4. Loop: receive "media" → decode → feed to session → send TTS response
      5. On "stop" → finalise session → enqueue call in main pipeline

    Args:
        websocket: FastAPI WebSocket connection from Twilio.
    """
    raise NotImplementedError


def decode_mulaw(payload_b64: str) -> bytes:
    """
    Decode a base64 μ-law audio chunk to raw PCM bytes.

    Twilio sends 8-bit μ-law at 8000 Hz. Most STT providers expect
    16-bit PCM at 8000 or 16000 Hz — this function handles the μ-law
    to linear PCM conversion.

    Args:
        payload_b64: Base64-encoded μ-law audio from Twilio media event.

    Returns:
        Raw PCM 16-bit little-endian bytes at 8000 Hz.
    """
    raise NotImplementedError


def encode_mulaw(pcm_bytes: bytes) -> str:
    """
    Encode PCM bytes to base64 μ-law for Twilio media send.

    Args:
        pcm_bytes: Raw PCM 16-bit bytes.

    Returns:
        Base64-encoded μ-law string for Twilio "media" send event.
    """
    raise NotImplementedError
