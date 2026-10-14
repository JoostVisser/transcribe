"""Mistral API client for transcription."""

from pathlib import Path
from typing import Any

import httpx
from mistralai.client import Mistral, errors

from transcribe.types import ProviderName, Segment, TranscriptionError

DEFAULT_MODEL = "voxtral-mini-latest"
CHUNK_SECONDS = 600  # 10 minutes per request
MAX_BIAS_TERMS = 100  # API limit for context_bias phrases.
_ERRORS = (
    errors.SDKError,
    errors.HTTPValidationError,
    errors.ResponseValidationError,
    errors.NoResponseError,
    httpx.HTTPError,
)


class MistralProvider:
    """Transcribes with Mistral's Voxtral models."""

    name = ProviderName.MISTRAL
    chunk_seconds = CHUNK_SECONDS
    max_bias_terms = MAX_BIAS_TERMS

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self.client = Mistral(api_key=api_key)
        self.model = model
        self.cost: float | None = None  # Mistral doesn't report it per request

    def standard(self, audio: Path, bias_terms: list[str] | None) -> str:
        """Return the full transcription text without timestamps or speaker labels."""
        response = self._complete(audio, context_bias=bias_terms)
        return response.text

    def segments(
        self, audio: Path, diarize: bool, bias_terms: list[str] | None
    ) -> list[Segment]:
        """Return transcription segments with timestamps and optional speaker
        labels."""
        response = self._complete(
            audio,
            diarize=diarize,
            context_bias=bias_terms,
            timestamp_granularities=["segment"],
        )

        if not response.segments:
            return []

        return [
            Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text,
                speaker_id=(
                    seg.speaker_id
                    if diarize and isinstance(seg.speaker_id, str)
                    else None
                ),
            )
            for seg in response.segments
        ]

    def _complete(self, audio: Path, **options: Any) -> Any:
        try:
            with audio.open("rb") as f:
                return self.client.audio.transcriptions.complete(
                    model=self.model,
                    file={"content": f, "file_name": "transcription.mp3"},
                    **options,
                )
        except _ERRORS as e:
            raise TranscriptionError(f"Mistral: {e}") from None
