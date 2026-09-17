"""CLI for transcribing audio and video files."""

from pathlib import Path
from typing import Annotated

import typer

from transcribe.transcribe import transcribe_file
from transcribe.types import TranscriptionKind

MAX_BIAS_TERMS = 100  # API limit for context_bias phrases.

app = typer.Typer(help="Transcribe audio and video files using Mistral's Voxtral API.")


@app.command()
def run(
    input_file: Annotated[
        Path,
        typer.Argument(exists=True, help="Path to the input video/audio file"),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Path where the transcription will be saved (.txt, .srt). "
                "For .srt, use --kind segmented (no speaker labels) "
                "or --kind annotated (with speaker labels)."
            )
        ),
    ],
    kind: Annotated[
        TranscriptionKind, typer.Option(help="standard, segmented, annotated)")
    ] = TranscriptionKind.SEGMENTED,
    bias: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            help=(
                "Glossary file with one term per line (blank lines and "
                "# comments are ignored) passed to the API as context_bias."
            ),
        ),
    ] = None,
) -> None:
    """Transcribe a video or audio file to text.

    Args:
        input_file: Path to the input video or audio file.
        output_file: Path where the transcription will be saved.
        kind: Type of transcription to perform: standard, segmented, annotated.
        bias: Optional glossary file used to bias spelling of proper nouns.
    """
    bias_terms = load_bias_terms(bias) if bias else None
    transcribe_file(input_file, output_file, kind, bias_terms)


def load_bias_terms(path: Path) -> list[str]:
    """Load glossary terms from a file, one term per line."""
    terms = [
        stripped
        for line in path.read_text(encoding="utf-8").splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
    ]
    if len(terms) > MAX_BIAS_TERMS:
        typer.echo(
            f"Error: {path} contains {len(terms)} terms; "
            f"the API allows at most {MAX_BIAS_TERMS}.",
            err=True,
        )
        raise typer.Exit(1)
    return terms


def cli() -> None:
    """Entry point for the transcribe CLI."""
    app()


if __name__ == "__main__":
    cli()
