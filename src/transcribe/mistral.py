"""Mistral API client for transcription."""

from pathlib import Path

import typer
from mistralai.client import Mistral

from transcribe.settings import settings
from transcribe.types import TranscriptionKind

API_URL = "https://api.mistral.ai/v1/audio/transcriptions"
MODEL = "voxtral-mini-latest"


class TranscriptionError(Exception):
    """Raised when transcription fails."""


def transcribe_to(
    audio_path: str | Path, output_path: str | Path, kind: TranscriptionKind
) -> None:
    """Transcribe an audio file using Mistral's Voxtral model.

    Args:
        audio_path: Path to the audio file to transcribe.
        output_path: Path where the transcription will be saved.
        kind: Type of transcription to perform: standard, segmented, annotated.

    Raises:
        TranscriptionError: If the API request fails.
        FileNotFoundError: If the audio file doesn't exist.
    """
    audio = Path(audio_path)
    output = Path(output_path)

    client = Mistral(api_key=settings.mistral_api_key)

    if not audio.exists():
        raise FileNotFoundError(f"Audio file not found: {audio}")

    if kind is TranscriptionKind.STANDARD:
        typer.echo("Performing standard transcription...")
        text = _standard_transcription(client, audio)
    else:
        typer.echo("Performing segmented transcription...")
        should_diarize = kind is TranscriptionKind.ANNOTATED
        text = _segmented_transcription(client, audio, should_diarize)

    output.write_text(text, encoding="utf-8")


def _standard_transcription(client: Mistral, audio: Path) -> str:
    """Perform a standard transcription without timestamps or speaker labels."""
    with audio.open("rb") as f:
        response = client.audio.transcriptions.complete(
            model=MODEL,
            file={
                "content": f,
                "file_name": "transcription.wav",
            },
        )
        return response.text


def _segmented_transcription(client: Mistral, audio: Path, diarize: bool) -> str:
    """Perform a segmented transcription with timestamps for each segment."""
    with audio.open("rb") as f:
        response = client.audio.transcriptions.complete(
            model=MODEL,
            file={
                "content": f,
                "file_name": "transcription.wav",
            },
            diarize=diarize,
            timestamp_granularities=["segment"],
        )

        text = ""

    if not response.segments:
        raise TranscriptionError("No segments found in transcription response.")

    for segment in response.segments:
        speaker = f" {segment.speaker_id}" or " unknown" if diarize else ""
        line = (
            f"[{segment.start:.1f}s → {segment.end:.1f}s]"
            f"{speaker}: {segment.text.strip()}"
        )
        text += line + "\n"

    return text.strip()
