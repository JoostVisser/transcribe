"""Audio conversion utilities."""

import subprocess
from functools import cache
from pathlib import Path

from static_ffmpeg import run as _ffmpeg_run


class ConversionError(Exception):
    """Raised when audio conversion fails."""


def convert_to_mp3(input_path: str | Path, output_path: str | Path) -> None:
    """Convert audio/video file to MP3 format using ffmpeg.

    Args:
        input_path: Path to the input audio or video file.
        output_path: Path where the MP3 file will be saved.

    Raises:
        ConversionError: If ffmpeg conversion fails.
        FileNotFoundError: If ffmpeg is not found or input file doesn't exist.
    """
    input = Path(input_path)
    output = Path(output_path)

    if not input.exists():
        raise FileNotFoundError(f"Input file not found: {input}")

    cmd = [
        _ffmpeg(),
        "-i",
        str(input),
        "-vn",  # No video
        "-acodec",
        "libmp3lame",
        "-b:a",
        "64k",  # 64 kbps — adequate for speech, ~4.8 MB/10 min
        "-ac",
        "1",  # Mono
        "-y",  # Overwrite output file
        str(output),
    ]

    try:
        _ = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise ConversionError(f"ffmpeg failed: {e.stderr}") from e


CHUNK_SECONDS = 600  # 10 minutes per chunk


def split_mp3(
    input_path: Path, output_dir: Path, chunk_seconds: int = CHUNK_SECONDS
) -> list[Path]:
    """Split an MP3 file into fixed-duration chunks using ffmpeg.

    Args:
        input_path: Path to the MP3 file to split.
        output_dir: Directory to save chunk files.
        chunk_seconds: Duration of each chunk in seconds.

    Returns:
        List of chunk file paths sorted by index.

    Raises:
        ConversionError: If ffmpeg splitting fails.
        FileNotFoundError: If ffmpeg is not found.
    """
    pattern = str(output_dir / "chunk_%03d.mp3")
    cmd = [
        _ffmpeg(),
        "-i",
        str(input_path),
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-c",
        "copy",
        "-y",
        pattern,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise ConversionError(f"ffmpeg split failed: {e.stderr}") from e
    return sorted(output_dir.glob("chunk_*.mp3"))


@cache
def _ffmpeg() -> str:
    """Return the path to the ffmpeg binary, downloading it if necessary."""
    ffmpeg, _ = _ffmpeg_run.get_or_fetch_platform_executables_else_raise()  # pyright: ignore[reportUnknownMemberType]
    return str(ffmpeg)
