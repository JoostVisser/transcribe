"""Mistral API client for transcription."""

from pathlib import Path

from mistralai.client import Mistral

from transcribe.settings import settings
from transcribe.types import Segment

MODEL = "voxtral-mini-latest"


class TranscriptionError(Exception):
    """Raised when transcription fails."""


def get_standard_transcription(audio: Path) -> str:
    """Return the full transcription text without timestamps or speaker labels."""
    client = Mistral(api_key=settings.mistral_api_key)
    with audio.open("rb") as f:
        response = client.audio.transcriptions.complete(
            model=MODEL,
            file={"content": f, "file_name": "transcription.mp3"},
        )
    return response.text


def get_segments(audio: Path, diarize: bool) -> list[Segment]:
    """Return transcription segments with timestamps and optional speaker labels."""
    client = Mistral(api_key=settings.mistral_api_key)
    with audio.open("rb") as f:
        response = client.audio.transcriptions.complete(
            model=MODEL,
            file={"content": f, "file_name": "transcription.mp3"},
            diarize=diarize,
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
                seg.speaker_id if diarize and isinstance(seg.speaker_id, str) else None
            ),
        )
        for seg in response.segments
    ]
