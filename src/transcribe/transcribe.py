"""Transcribe audio or video files using Mistral."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import typer

from transcribe.audio import ConversionError, convert_to_wav
from transcribe.mistral import TranscriptionError, transcribe_to
from transcribe.types import TranscriptionKind


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

    typer.echo(f"Converting {input_path.name} to WAV...")

    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            wav_path = Path(temp_wav.name)
            convert_to_wav(input_path, wav_path)
    except ConversionError as e:
        typer.echo(f"Error converting file: {e}", err=True)
        raise typer.Exit(1) from None
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    try:
        typer.echo("Transcribing...")
        transcribe_to(wav_path, output_path, kind)

        # output_path.write_text(text, encoding="utf-8")
        typer.echo(f"Transcription saved to {output_path}")
    except TranscriptionError as e:
        typer.echo(f"Error transcribing: {e}", err=True)
        raise typer.Exit(1) from None
    finally:
        wav_path.unlink(missing_ok=True)
