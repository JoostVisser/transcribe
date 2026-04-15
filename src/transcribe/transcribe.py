"""Transcribe audio or video files using Mistral."""

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import typer

from transcribe import formats
from transcribe.audio import CHUNK_SECONDS, ConversionError, convert_to_mp3, split_mp3
from transcribe.mistral import (
    TranscriptionError,
    get_segments,
    get_standard_transcription,
)
from transcribe.types import Segment, TranscriptionKind

_CHUNK_SIZE_THRESHOLD = 20 * 1024 * 1024  # 20 MB


def transcribe_file(
    input_path: Path, output_path: Path, kind: TranscriptionKind
) -> None:
    """Convert input file to WAV and transcribe it.

    Args:
        input_path: Path to the input audio or video file.
        output_path: Path where the transcription will be saved.
        kind: Type of transcription to perform: standard, segmented, annotated.

    Raises:
        typer.Exit: If conversion or transcription fails.
    """
    if not input_path.exists():
        typer.echo(f"Error: Input file not found: {input_path}", err=True)
        raise typer.Exit(1)

    is_srt = output_path.suffix.lower() == ".srt"

    if is_srt and kind is TranscriptionKind.STANDARD:
        typer.echo(
            "Error: SRT output requires timestamps. "
            "Use --kind segmented or --kind annotated.",
            err=True,
        )
        raise typer.Exit(1)

    typer.echo(f"Converting {input_path.name} to MP3...")

    try:
        with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3:
            mp3_path = Path(temp_mp3.name)
            convert_to_mp3(input_path, mp3_path)
    except ConversionError as e:
        typer.echo(f"Error converting file: {e}", err=True)
        raise typer.Exit(1) from None
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    try:
        if mp3_path.stat().st_size > _CHUNK_SIZE_THRESHOLD:
            typer.echo("Large file detected, splitting into chunks...")
            text = _transcribe_chunks(mp3_path, kind, is_srt)
        else:
            typer.echo("Transcribing...")
            text = _transcribe_mp3(mp3_path, kind, is_srt)

        output_path.write_text(text, encoding="utf-8")
        typer.echo(f"Transcription saved to {output_path}")
    except TranscriptionError as e:
        typer.echo(f"Error transcribing: {e}", err=True)
        raise typer.Exit(1) from None
    finally:
        mp3_path.unlink(missing_ok=True)


def _transcribe_mp3(mp3_path: Path, kind: TranscriptionKind, is_srt: bool) -> str:
    """Transcribe a single MP3 file and return the formatted result."""
    if kind is TranscriptionKind.STANDARD:
        return get_standard_transcription(mp3_path)
    diarize = kind is TranscriptionKind.ANNOTATED
    segments = get_segments(mp3_path, diarize)
    if not segments:
        raise TranscriptionError("No segments found in transcription response.")
    return formats.to_srt(segments) if is_srt else formats.to_annotated_text(segments)


def _transcribe_chunks(mp3_path: Path, kind: TranscriptionKind, is_srt: bool) -> str:
    """Split MP3 into chunks, transcribe each, and combine results."""
    with TemporaryDirectory() as tmp_dir:
        chunks = split_mp3(mp3_path, Path(tmp_dir))
        typer.echo(f"Split into {len(chunks)} chunks.")

        if kind is TranscriptionKind.STANDARD:
            texts: list[str] = []
            for i, chunk in enumerate(chunks, start=1):
                typer.echo(f"  Transcribing chunk {i}/{len(chunks)}...")
                texts.append(get_standard_transcription(chunk))
            return " ".join(texts)

        diarize = kind is TranscriptionKind.ANNOTATED
        all_segments: list[Segment] = []
        for i, chunk in enumerate(chunks):
            typer.echo(f"  Transcribing chunk {i + 1}/{len(chunks)}...")
            offset = i * CHUNK_SECONDS
            for seg in get_segments(chunk, diarize):
                all_segments.append(
                    Segment(
                        start=seg.start + offset,
                        end=seg.end + offset,
                        text=seg.text,
                        speaker_id=seg.speaker_id,
                    )
                )
        if not all_segments:
            raise TranscriptionError("No segments found in any chunk.")
        return (
            formats.to_srt(all_segments)
            if is_srt
            else formats.to_annotated_text(all_segments)
        )
