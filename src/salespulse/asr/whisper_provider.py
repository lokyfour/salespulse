"""
asr/whisper_provider.py

Local ASR provider using faster-whisper (CTranslate2 backend).

Runs entirely on-prem — no audio data leaves the machine.
Suitable for deployments with data-residency requirements (GDPR Art. 28).

Performance reference (large-v3 model):
  - GPU (A10G):  ~1 min of audio per 6 seconds of processing
  - CPU (int8):  ~1 min of audio per 10–12 seconds of processing

Interface:
    WhisperLocalProvider.transcribe(path, config) -> RawTranscript
"""

from __future__ import annotations

from pathlib import Path

from .base import ASRConfig, ASRProvider, RawTranscript


class WhisperLocalProvider(ASRProvider):
    """
    faster-whisper wrapper. Downloads the model on first use and caches
    it at `~/.cache/huggingface/hub/` (or $HF_HOME if set).

    Configuration:
        model:        Whisper model size (tiny/base/small/medium/large-v3)
        compute_type: "int8" for CPU, "float16" for GPU
        device:       "cpu" | "cuda" | "auto"
    """

    def __init__(self, device: str = "auto") -> None:
        """
        Args:
            device: Compute device. "auto" selects CUDA if available, else CPU.
        """
        self._device = device
        self._model = None  # Loaded lazily on first transcribe() call

    @property
    def provider_name(self) -> str:
        return "whisper_local"

    def transcribe(self, path: Path, config: ASRConfig) -> RawTranscript:
        """
        Transcribe `path` using the configured faster-whisper model.

        Loads the model on first call; subsequent calls reuse the loaded model.
        Word-level timestamps are always enabled.

        Args:
            path: Path to 16 kHz mono WAV.
            config: ASR config with model size, compute type, language.

        Returns:
            RawTranscript with word-level tokens.
        """
        raise NotImplementedError

    def _load_model(self, model_name: str, compute_type: str) -> None:
        """
        Load the faster-whisper model into memory.
        Called once and cached in self._model.
        """
        raise NotImplementedError
