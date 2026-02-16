"""CLI for transcribing audio and video files."""

from pathlib import Path
from typing import Annotated

import typer

from transcribe.transcribe import transcribe_file
from transcribe.types import TranscriptionKind

app = typer.Typer(help="Transcribe audio and video files using Mistral's Voxtral API.")


@app.command()
def run(
    input_file: Annotated[
        Path,
        typer.Argument(exists=True, help="Path to the input video/audio file"),
    ],
    output_text: Annotated[
        Path,
        typer.Argument(help="Path where the transcription will be saved"),
    ],
    kind: Annotated[
        TranscriptionKind, typer.Option(help="standard, segmented, annotated)")
    ] = TranscriptionKind.STANDARD,
) -> None:
    """Transcribe a video or audio file to text.

    Args:
        input_file: Path to the input video or audio file.
        output_text: Path where the transcription will be saved.
        kind: Type of transcription to perform: standard, segmented, annotated.
    """
    transcribe_file(input_file, output_text, kind)


def cli() -> None:
    """Entry point for the transcribe CLI."""
    app()


if __name__ == "__main__":
    cli()
