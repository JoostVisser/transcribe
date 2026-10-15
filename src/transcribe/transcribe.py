"""Transcribe audio or video files."""

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import typer

from transcribe import formats
from transcribe.audio import ConversionError, convert_to_mp3, split_mp3
from transcribe.types import Provider, Segment, TranscriptionError, TranscriptionKind


def transcribe_file(
    input_path: Path,
    output_path: Path,
    kind: TranscriptionKind,
    provider: Provider,
    bias_terms: list[str] | None = None,
) -> None:
    """Convert input file to MP3 and transcribe it.

    Args:
        input_path: Path to the input audio or video file.
        output_path: Path where the transcription will be saved.
        kind: Type of transcription to perform: standard, segmented, annotated.
        provider: The transcription API to call.
        bias_terms: Optional glossary terms to bias the spelling of proper nouns.

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
        typer.echo(f"Transcribing with {provider.model} ({provider.name})...")
        text = _transcribe_mp3(mp3_path, kind, is_srt, provider, bias_terms)
        output_path.write_text(text, encoding="utf-8")
        typer.echo(f"Transcription saved to {output_path}")
        if provider.cost is not None:
            typer.echo(f"Cost: ${provider.cost:.4f}")
    except (TranscriptionError, ConversionError) as e:
        typer.echo(f"Error transcribing: {e}", err=True)
        raise typer.Exit(1) from None
    finally:
        mp3_path.unlink(missing_ok=True)


def _transcribe_mp3(
    mp3_path: Path,
    kind: TranscriptionKind,
    is_srt: bool,
    provider: Provider,
    bias_terms: list[str] | None,
) -> str:
    """Split the MP3 into the chunks the provider takes, transcribe each and
    combine the results."""
    with TemporaryDirectory() as tmp_dir:
        chunks = split_mp3(mp3_path, Path(tmp_dir), provider.chunk_seconds)
        if len(chunks) > 1:
            typer.echo(f"Split into {len(chunks)} chunks.")

        if kind is TranscriptionKind.STANDARD:
            texts: list[str] = []
            for i, chunk in enumerate(chunks, start=1):
                _progress(i, chunks)
                texts.append(provider.standard(chunk, bias_terms))
            text = " ".join(text.strip() for text in texts if text.strip())
            if not text:
                typer.echo("No speech found.")
            return text

        diarize = kind is TranscriptionKind.ANNOTATED
        all_segments: list[Segment] = []
        for i, chunk in enumerate(chunks):
            _progress(i + 1, chunks)
            offset = i * provider.chunk_seconds
            all_segments += [
                seg.shifted(offset)
                for seg in provider.segments(chunk, diarize, bias_terms)
            ]
    if not all_segments:
        # Wind, music or a motor: nothing to say is a result, not a failure.
        typer.echo("No speech found.")
        return ""
    return (
        formats.to_srt(all_segments)
        if is_srt
        else formats.to_annotated_text(all_segments)
    )


def _progress(i: int, chunks: list[Path]) -> None:
    if len(chunks) > 1:
        typer.echo(f"  Transcribing chunk {i}/{len(chunks)}...")
